"""Lender-facing portfolio, signal, alert, and read-only review endpoints."""

from __future__ import annotations

import json
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..authz import require_lender
from ..config import settings
from ..db import get_db
from ..models import Alert, Consent, LenderAction, LenderPortfolio, Loan, Merchant, Payment, Transaction
from ..schemas import LenderActionRequest
from ..services.audit import create_audit_record
from ..services.alerts import consent_is_active, effective_as_of, evaluate_merchant_alerts, merchant_signal_evaluation, repayment_summary
from ..services.forecast import forecast_transactions
from ..services.summary import monthly_summary
from ..services.weekly import weekly_cash_flow
from ..services.signals import render_signal_reason
from ..services.explain import explain_recommendation_translated
from ..i18n import t
from .helpers import decimal, response
from .loan import loan_payload

router = APIRouter(prefix="/lender", tags=["lender"])


def portfolio_merchants(db: Session, lender_id: int) -> list[Merchant]:
    return [
        item.merchant
        for item in db.query(LenderPortfolio).filter(LenderPortfolio.lender_id == lender_id).all()
        if item.merchant is not None
    ]


def consent_for(db: Session, merchant_id: int) -> Consent | None:
    return db.query(Consent).filter(Consent.merchant_id == merchant_id).order_by(Consent.id.desc()).first()


def consent_payload(consent: Consent | None) -> dict:
    return {
        "status": consent.status if consent else "unknown",
        "scope": consent.scope if consent else "transaction history",
        "granted_at": consent.granted_at.isoformat() if consent else None,
        "expires_at": consent.expires_at.isoformat() if consent and consent.expires_at else None,
        "revoked_at": consent.revoked_at.isoformat() if consent and consent.revoked_at else None,
    }


def loan_dict(loan: Loan | None) -> dict | None:
    if loan is None:
        return None
    return {"standard_emi": float(loan.standard_emi), "min_emi": float(loan.min_emi), "max_emi": float(loan.max_emi)}


def merchant_review(db: Session, merchant: Merchant, as_of: date | None = None, lang: str | None = None) -> dict:
    effective = effective_as_of(db, as_of)
    consent = consent_for(db, merchant.id)
    if not consent_is_active(consent, effective):
        return {"merchant": {"id": merchant.id, "name": merchant.name, "city": merchant.city}, "status": "consent withdrawn", "consent": consent_payload(consent)}
    records = db.query(Transaction).filter(Transaction.merchant_id == merchant.id, Transaction.transaction_date <= effective).all()
    evaluation = merchant_signal_evaluation(db, merchant, effective)
    loan = db.query(Loan).filter(Loan.merchant_id == merchant.id).first()
    payments = db.query(Payment).filter(Payment.loan_id == loan.id).order_by(Payment.due_date, Payment.id).all() if loan else []
    forecast = forecast_transactions(records, horizon_days=28, prefer_prophet=settings.use_prophet)
    selected_lang = lang if lang in {"en", "hi", "bn"} else merchant.preferred_language
    signal_payload = {**evaluation["signals"], "signals": [render_signal_reason(item, selected_lang) for item in evaluation["signals"]["signals"]]}
    return {
        "merchant": {"id": merchant.id, "name": merchant.name, "city": merchant.city, "business_type": merchant.business_type, "preferred_language": merchant.preferred_language, "scenario": merchant.scenario},
        "status": evaluation["signals"]["status"],
        "consent": consent_payload(consent),
        "weekly": evaluation["weekly"],
        "monthly_summary": monthly_summary(records),
        "signals": signal_payload,
        "forecast": {"label": "estimate, not a guarantee", **forecast.as_dict()},
        "repayment": {"history": [{"due_date": item.due_date.isoformat() if item.due_date else None, "payment_date": item.payment_date.isoformat() if item.payment_date else None, "amount": decimal(item.amount), "status": item.status, "days_late": item.days_late, "balance_after": decimal(item.balance_after)} for item in payments], **evaluation["repayment"]},
        "emi_suggestion": {"label": "suggestion for lender review; Cashira does not change any EMI", "loan": loan_payload(loan) if loan else None, "explanation": explain_recommendation_translated([], selected_lang)},
        "alerts": [{"id": item.id, "signal_id": item.signal_id, "severity": item.severity, "status": item.status, "week_key": item.week_key, "message_key": item.message_key, "params": json.loads(item.params_json)} for item in db.query(Alert).filter(Alert.merchant_id == merchant.id).order_by(Alert.id).all()],
    }


@router.post("/evaluate")
def evaluate(as_of: date | None = Query(default=None), identity: dict = Depends(require_lender), db: Session = Depends(get_db)) -> dict:
    effective = effective_as_of(db, as_of)
    evaluated = []
    for merchant in portfolio_merchants(db, identity["lender_id"]):
        consent = consent_for(db, merchant.id)
        if consent_is_active(consent, effective):
            evaluated.append(evaluate_merchant_alerts(db, merchant, effective))
    db.commit()
    return response({"as_of": effective.isoformat(), "merchants_evaluated": len(evaluated), "alerts": sum(len(item["alerts"]) for item in evaluated)})


@router.get("/portfolio")
def portfolio(as_of: date | None = Query(default=None), identity: dict = Depends(require_lender), db: Session = Depends(get_db)) -> dict:
    effective = effective_as_of(db, as_of)
    merchants = portfolio_merchants(db, identity["lender_id"])
    for merchant in merchants:
        if consent_is_active(consent_for(db, merchant.id), effective):
            evaluate_merchant_alerts(db, merchant, effective)
    db.commit()
    items = []
    counts = {"green": 0, "amber": 0, "red": 0, "consent withdrawn": 0}
    for merchant in merchants:
        consent = consent_for(db, merchant.id)
        if not consent_is_active(consent, effective):
            item = {"id": merchant.id, "name": merchant.name, "city": merchant.city, "status": "consent withdrawn", "consent_status": consent.status if consent else "unknown"}
            counts["consent withdrawn"] += 1
            items.append(item)
            continue
        evaluation = merchant_signal_evaluation(db, merchant, effective)
        loan = evaluation["loan"]
        repayment = evaluation["repayment"]
        alerts = db.query(Alert).filter(Alert.merchant_id == merchant.id, Alert.status.in_(["new", "acknowledged"])).all()
        status = evaluation["signals"]["status"]
        counts[status] += 1
        items.append({"id": merchant.id, "name": merchant.name, "city": merchant.city, "status": status, "four_week_sales_change": evaluation["weekly"]["four_week_sales_change"], "emi_coverage": next((signal["params"].get("coverage") for signal in evaluation["signals"]["signals"] if signal["id"] == "S3"), None), "open_alerts": len(alerts), "next_due": _next_due(loan, effective).isoformat() if loan else None, "days_overdue": repayment["days_overdue"], "consent_status": consent.status})
    return response({"as_of": effective.isoformat(), "counts": counts, "merchants": items})


def _next_due(loan: Loan | None, as_of: date) -> date:
    if loan is None:
        return as_of
    year, month = as_of.year, as_of.month
    if as_of.day >= loan.due_day:
        month += 1
        if month == 13:
            month, year = 1, year + 1
    return date(year, month, min(loan.due_day, 28))


@router.get("/merchants/{merchant_id}")
def merchant_detail(merchant_id: int, as_of: date | None = Query(default=None), lang: str | None = Query(default=None), identity: dict = Depends(require_lender), db: Session = Depends(get_db)) -> dict:
    merchant = next((item for item in portfolio_merchants(db, identity["lender_id"]) if item.id == merchant_id), None)
    if merchant is None:
        raise HTTPException(status_code=404, detail="Merchant is not in lender portfolio")
    return response(merchant_review(db, merchant, as_of, lang))


@router.get("/alerts")
def alerts(status: str | None = None, severity: str | None = None, identity: dict = Depends(require_lender), db: Session = Depends(get_db)) -> dict:
    merchant_ids = [item.id for item in portfolio_merchants(db, identity["lender_id"]) if consent_is_active(consent_for(db, item.id), effective_as_of(db))]
    query = db.query(Alert).filter(Alert.merchant_id.in_(merchant_ids))
    if status:
        query = query.filter(Alert.status == status)
    if severity:
        query = query.filter(Alert.severity == severity)
    return response({"alerts": [{"id": item.id, "merchant_id": item.merchant_id, "signal_id": item.signal_id, "severity": item.severity, "week_key": item.week_key, "status": item.status, "message_key": item.message_key, "params": json.loads(item.params_json), "rule_version": item.rule_version} for item in query.order_by(Alert.id.desc()).all()]})


@router.post("/alerts/{alert_id}/{action}")
def alert_action(alert_id: int, action: str, identity: dict = Depends(require_lender), db: Session = Depends(get_db)) -> dict:
    if action not in {"acknowledge", "dismiss"}:
        raise HTTPException(status_code=404, detail="Unknown alert action")
    alert = db.get(Alert, alert_id)
    portfolio_ids = {item.id for item in portfolio_merchants(db, identity["lender_id"])}
    if alert is None or alert.merchant_id not in portfolio_ids or not consent_is_active(consent_for(db, alert.merchant_id), effective_as_of(db)):
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = "acknowledged" if action == "acknowledge" else "dismissed"
    db.commit()
    return response({"alert_id": alert.id, "status": alert.status})


@router.post("/merchants/{merchant_id}/actions")
def create_action(merchant_id: int, payload: LenderActionRequest, identity: dict = Depends(require_lender), db: Session = Depends(get_db)) -> dict:
    if payload.type not in {"reminder", "contact", "review"}:
        raise HTTPException(status_code=422, detail="Action type must be reminder, contact, or review")
    merchant = next((item for item in portfolio_merchants(db, identity["lender_id"]) if item.id == merchant_id), None)
    effective = effective_as_of(db)
    if merchant is None or not consent_is_active(consent_for(db, merchant_id), effective):
        raise HTTPException(status_code=404, detail="Merchant is not available for lender action")
    language = payload.lang if payload.lang in {"en", "hi", "bn"} else merchant.preferred_language
    key = f"reminders.{payload.type}" if payload.type in {"reminder", "contact", "review"} else "reminders.contact"
    params = {"name": merchant.name, "amount": float(merchant.loans[0].standard_emi) if merchant.loans else 0}
    action = LenderAction(lender_id=identity["lender_id"], merchant_id=merchant_id, action_type=payload.type, note=payload.note, alert_id=payload.alert_id, language=language, message_key=key, message_params_json=json.dumps(params, sort_keys=True), message_text=t(key, language, **params))
    db.add(action)
    db.flush()
    loan = merchant.loans[0] if merchant.loans else None
    if loan:
        audit = create_audit_record(db, loan_id=loan.id, record_type="lender_action", record={"action_id": action.id, "merchant_id": merchant_id, "action_type": payload.type, "note": payload.note, "message_key": key, "language": language}, rule_version="cashira-action-v1")
    db.commit()
    return response({"action_id": action.id, "type": action.action_type, "message_key": action.message_key, "params": params, "language": language, "text": action.message_text, "sent": False, "audit_record_id": audit.id if loan else None})


@router.get("/merchants/{merchant_id}/actions")
def list_actions(merchant_id: int, identity: dict = Depends(require_lender), db: Session = Depends(get_db)) -> dict:
    portfolio_ids = {item.id for item in portfolio_merchants(db, identity["lender_id"])}
    if merchant_id not in portfolio_ids or not consent_is_active(consent_for(db, merchant_id), effective_as_of(db)):
        raise HTTPException(status_code=404, detail="Merchant is not available for lender action")
    actions = db.query(LenderAction).filter(LenderAction.merchant_id == merchant_id).order_by(LenderAction.id.desc()).all()
    return response({"actions": [{"id": item.id, "type": item.action_type, "note": item.note, "message_key": item.message_key, "params": json.loads(item.message_params_json), "language": item.language, "text": item.message_text, "created_at": item.created_at.isoformat()} for item in actions]})
