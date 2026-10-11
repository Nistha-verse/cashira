"""Lender-facing portfolio, signal, alert, and read-only review endpoints."""

from __future__ import annotations

import json
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..authz import require_lender
from ..config import settings
from ..db import get_db
from ..models import Alert, AuditRecord, Consent, LenderAction, LenderPortfolio, Loan, Merchant, Payment, Transaction
from ..schemas import LenderActionRequest
from ..services.audit import create_audit_record
from ..services.alerts import consent_is_active, effective_as_of, evaluate_merchant_alerts, merchant_signal_evaluation, repayment_summary
from ..services.forecast import forecast_transactions
from ..services.summary import monthly_summary
from ..services.weekly import weekly_cash_flow
from ..services.signals import render_signal_reason
from ..services.priority import PRIORITY_RANK, days_until_due, next_due_date, priority_for
from ..services.why_flagged import build_why_flagged
from ..services.explain import explain_recommendation_translated
from ..i18n import t
from .helpers import decimal, record_info, response
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
        return {"merchant": {"id": merchant.id, "name": merchant.name, "city": merchant.city}, "status": "consent withdrawn", "priority": "consent withdrawn", "days_until_due": None, "data_as_of": effective.isoformat(), "consent": consent_payload(consent)}
    records = db.query(Transaction).filter(Transaction.merchant_id == merchant.id, Transaction.transaction_date <= effective).all()
    evaluation = merchant_signal_evaluation(db, merchant, effective)
    loan = db.query(Loan).filter(Loan.merchant_id == merchant.id).first()
    payments = db.query(Payment).filter(Payment.loan_id == loan.id).order_by(Payment.due_date, Payment.id).all() if loan else []
    forecast = forecast_transactions(records, horizon_days=28, prefer_prophet=settings.use_prophet)
    selected_lang = lang if lang in {"en", "hi", "bn"} else merchant.preferred_language
    signal_payload = {**evaluation["signals"], "signals": [render_signal_reason(item, selected_lang) for item in evaluation["signals"]["signals"]]}
    due_days = days_until_due(loan, effective)
    priority = priority_for(evaluation["signals"]["status"], due_days)
    why_flagged = build_why_flagged(records, evaluation, loan, effective)
    return {
        "merchant": {"id": merchant.id, "name": merchant.name, "city": merchant.city, "business_type": merchant.business_type, "preferred_language": merchant.preferred_language, "scenario": merchant.scenario},
        "status": evaluation["signals"]["status"],
        "priority": priority,
        "days_until_due": due_days,
        "data_as_of": effective.isoformat(),
        "consent": consent_payload(consent),
        "weekly": evaluation["weekly"],
        "monthly_summary": monthly_summary(records),
        "signals": signal_payload,
        "data_coverage": evaluation["data_coverage"],
        "why_flagged": why_flagged,
        "forecast": {"label": "estimate, not a guarantee", **forecast.as_dict()},
        "repayment": {"history": [{"due_date": item.due_date.isoformat() if item.due_date else None, "payment_date": item.payment_date.isoformat() if item.payment_date else None, "amount": decimal(item.amount), "status": item.status, "status_key": f"repayment.{item.status}", "status_text": t(f"repayment.{item.status}", selected_lang), "days_late": item.days_late, "balance_after": decimal(item.balance_after)} for item in payments], **evaluation["repayment"]},
        "emi_suggestion": {"label": "suggestion for lender review; Cashira does not change any EMI", "loan": loan_payload(loan) if loan else None, "explanation": explain_recommendation_translated([], selected_lang)},
        "alerts": [{"id": item.id, "signal_id": item.signal_id, "severity": item.severity, "status": item.status, "action_id": item.action_id, "week_key": item.week_key, "message_key": item.message_key, "params": json.loads(item.params_json), "text": t(item.message_key, selected_lang, **json.loads(item.params_json)), "rule_version": item.rule_version} for item in db.query(Alert).filter(Alert.merchant_id == merchant.id).order_by(Alert.id).all()],
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
    return response({"as_of": effective.isoformat(), "data_as_of": effective.isoformat(), "merchants_evaluated": len(evaluated), "alerts": sum(len(item["alerts"]) for item in evaluated)})


@router.get("/portfolio")
def portfolio(as_of: date | None = Query(default=None), identity: dict = Depends(require_lender), db: Session = Depends(get_db)) -> dict:
    effective = effective_as_of(db, as_of)
    merchants = portfolio_merchants(db, identity["lender_id"])
    for merchant in merchants:
        if consent_is_active(consent_for(db, merchant.id), effective):
            evaluate_merchant_alerts(db, merchant, effective)
    db.commit()
    items = []
    counts = {"green": 0, "amber": 0, "red": 0, "high": 0, "medium": 0, "healthy": 0, "consent withdrawn": 0}
    priority_counts = {"high": 0, "medium": 0, "healthy": 0, "consent withdrawn": 0}
    for merchant in merchants:
        consent = consent_for(db, merchant.id)
        if not consent_is_active(consent, effective):
            item = {"id": merchant.id, "name": merchant.name, "city": merchant.city, "status": "consent withdrawn", "priority": "consent withdrawn", "days_until_due": None, "data_as_of": effective.isoformat(), "consent_status": consent.status if consent else "unknown"}
            counts["consent withdrawn"] += 1
            priority_counts["consent withdrawn"] += 1
            items.append(item)
            continue
        evaluation = merchant_signal_evaluation(db, merchant, effective)
        loan = evaluation["loan"]
        repayment = evaluation["repayment"]
        alerts = db.query(Alert).filter(Alert.merchant_id == merchant.id, Alert.status.in_(["new", "acknowledged"])).all()
        status = evaluation["signals"]["status"]
        due_days = days_until_due(loan, effective)
        priority = priority_for(status, due_days)
        counts[status] += 1
        counts[priority] += 1
        priority_counts[priority] += 1
        why = build_why_flagged(db.query(Transaction).filter(Transaction.merchant_id == merchant.id, Transaction.transaction_date <= effective).all(), evaluation, loan, effective)
        headline = why[0]["text"]["en"] if why else "No active reason was returned."
        actioned_alerts = db.query(Alert).filter(Alert.merchant_id == merchant.id, Alert.status == "actioned").count()
        items.append({"id": merchant.id, "name": merchant.name, "city": merchant.city, "status": status, "priority": priority, "days_until_due": due_days, "four_week_sales_change": evaluation["weekly"]["four_week_sales_change"], "emi_coverage": next((signal["params"].get("coverage") for signal in evaluation["signals"]["signals"] if signal["id"] == "S3"), None), "open_alerts": len(alerts), "actioned_alerts": actioned_alerts, "next_due": next_due_date(loan, effective).isoformat() if loan else None, "days_overdue": repayment["days_overdue"], "covered_days": evaluation["data_coverage"]["covered_days"], "window_days": evaluation["data_coverage"]["window_days"], "headline_reason": headline, "consent_status": consent.status, "data_as_of": effective.isoformat()})
    items.sort(key=lambda item: (PRIORITY_RANK[item["priority"]], item["days_until_due"] if item["days_until_due"] is not None else 9999, item["name"]))
    return response({"as_of": effective.isoformat(), "data_as_of": effective.isoformat(), "counts": counts, "priority_counts": priority_counts, "merchants": items})


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
def alerts(status: str | None = None, severity: str | None = None, lang: str = "en", identity: dict = Depends(require_lender), db: Session = Depends(get_db)) -> dict:
    merchant_ids = [item.id for item in portfolio_merchants(db, identity["lender_id"]) if consent_is_active(consent_for(db, item.id), effective_as_of(db))]
    query = db.query(Alert).filter(Alert.merchant_id.in_(merchant_ids))
    if status:
        query = query.filter(Alert.status == status)
    if severity:
        query = query.filter(Alert.severity == severity)
    selected_lang = lang if lang in {"en", "hi", "bn"} else "en"
    return response({"data_as_of": effective_as_of(db).isoformat(), "alerts": [{"id": item.id, "merchant_id": item.merchant_id, "signal_id": item.signal_id, "severity": item.severity, "week_key": item.week_key, "status": item.status, "action_id": item.action_id, "message_key": item.message_key, "params": json.loads(item.params_json), "text": t(item.message_key, selected_lang, **json.loads(item.params_json)), "rule_version": item.rule_version} for item in query.order_by(Alert.id.desc()).all()]})


@router.post("/alerts/{alert_id}/{action}")
def alert_action(alert_id: int, action: str, identity: dict = Depends(require_lender), db: Session = Depends(get_db)) -> dict:
    if action not in {"acknowledge", "dismiss"}:
        raise HTTPException(status_code=404, detail="Unknown alert action")
    alert = db.get(Alert, alert_id)
    portfolio_ids = {item.id for item in portfolio_merchants(db, identity["lender_id"])}
    if alert is None or alert.merchant_id not in portfolio_ids or not consent_is_active(consent_for(db, alert.merchant_id), effective_as_of(db)):
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = "acknowledged" if action == "acknowledge" else "dismissed"
    loan = db.query(Loan).filter(Loan.merchant_id == alert.merchant_id).first()
    audit = None
    if loan:
        audit = create_audit_record(db, loan_id=loan.id, record_type="alert_action", record={"alert_id": alert.id, "status": alert.status, "changed_by": "lender"}, rule_version="cashira-alert-v1")
        from ..services.anchor import anchor_audit_record
        anchor_audit_record(db, audit)
    db.commit()
    return response({"alert_id": alert.id, "status": alert.status, "action_id": alert.action_id, "audit_record_id": audit.id if audit else None, **record_info(audit)})


@router.post("/merchants/{merchant_id}/actions")
def create_action(merchant_id: int, payload: LenderActionRequest, identity: dict = Depends(require_lender), db: Session = Depends(get_db)) -> dict:
    if payload.type not in {"reminder", "contact", "review", "no_action"}:
        raise HTTPException(status_code=422, detail="Action type must be reminder, contact, review, or no_action")
    if payload.type == "no_action" and not payload.note.strip():
        raise HTTPException(status_code=422, detail="A note is required for no_action")
    merchant = next((item for item in portfolio_merchants(db, identity["lender_id"]) if item.id == merchant_id), None)
    effective = effective_as_of(db)
    if merchant is None or not consent_is_active(consent_for(db, merchant_id), effective):
        raise HTTPException(status_code=404, detail="Merchant is not available for lender action")
    language = payload.lang if payload.lang in {"en", "hi", "bn"} else merchant.preferred_language
    key = "reminders.payment" if payload.type == "reminder" else f"reminders.{payload.type}" if payload.type != "no_action" else None
    params = {"name": merchant.name, "amount": float(merchant.loans[0].standard_emi) if merchant.loans else 0}
    linked_alert = db.get(Alert, payload.alert_id) if payload.alert_id else None
    if linked_alert and (linked_alert.merchant_id != merchant_id or linked_alert.status == "dismissed"):
        raise HTTPException(status_code=422, detail="Linked alert is not available for this merchant")
    action = LenderAction(lender_id=identity["lender_id"], merchant_id=merchant_id, action_type=payload.type, note=payload.note, alert_id=payload.alert_id, language=language, message_key=key, message_params_json=json.dumps(params if key else {}, sort_keys=True), message_text=t(key, language, **params) if key else None)
    db.add(action)
    db.flush()
    loan = merchant.loans[0] if merchant.loans else None
    if loan:
        audit = create_audit_record(db, loan_id=loan.id, record_type="lender_action", record={"action_id": action.id, "merchant_id": merchant_id, "alert_id": payload.alert_id, "action_type": payload.type, "note": payload.note, "message_key": key, "language": language}, rule_version="cashira-action-v1")
        from ..services.anchor import anchor_audit_record
        anchor_audit_record(db, audit)
    else:
        audit = None
    if linked_alert:
        linked_alert.status = "actioned"
        linked_alert.action_id = action.id
    db.commit()
    return response({"action_id": action.id, "type": action.action_type, "message_key": action.message_key, "params": params if key else {}, "language": language, "text": action.message_text, "sent": False, "audit_record_id": audit.id if audit else None, **record_info(audit)})


@router.get("/merchants/{merchant_id}/actions")
def list_actions(merchant_id: int, identity: dict = Depends(require_lender), db: Session = Depends(get_db)) -> dict:
    portfolio_ids = {item.id for item in portfolio_merchants(db, identity["lender_id"])}
    if merchant_id not in portfolio_ids or not consent_is_active(consent_for(db, merchant_id), effective_as_of(db)):
        raise HTTPException(status_code=404, detail="Merchant is not available for lender action")
    actions = db.query(LenderAction).filter(LenderAction.merchant_id == merchant_id).order_by(LenderAction.id.desc()).all()
    audit_map = {}
    for audit in db.query(AuditRecord).filter(AuditRecord.record_type == "lender_action").all():
        try:
            payload = json.loads(audit.record_json)
            if payload.get("action_id"):
                audit_map[payload["action_id"]] = audit.id
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
    return response({"actions": [{"id": item.id, "type": item.action_type, "note": item.note, "alert_id": item.alert_id, "message_key": item.message_key, "params": json.loads(item.message_params_json), "language": item.language, "text": item.message_text, "created_at": item.created_at.isoformat(), "audit_record_id": audit_map.get(item.id)} for item in actions]})
