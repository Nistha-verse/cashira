from __future__ import annotations

import json
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Consent, LenderAction, Merchant, Transaction
from ..i18n import t
from ..models import Loan
from ..services.audit import create_audit_record
from ..authz import require_merchant
from ..services.forecast import forecast_transactions
from ..services.summary import monthly_summary
from ..config import settings
from .helpers import decimal, record_info, response
from ..services.alerts import effective_as_of
from ..services.anchor import anchor_audit_record

router = APIRouter(prefix="/merchant", tags=["merchant"])
DEMO_MERCHANT_ID = 1


def get_demo_merchant(db: Session, identity: dict | None = None) -> Merchant:
    merchant_id = (identity or {}).get("merchant_id", DEMO_MERCHANT_ID)
    merchant = db.get(Merchant, merchant_id)
    if merchant is None:
        raise HTTPException(status_code=404, detail="Demo merchant is not seeded")
    return merchant


def get_demo_records(db: Session, from_date: date | None = None, to_date: date | None = None, merchant_id: int = DEMO_MERCHANT_ID) -> list[Transaction]:
    merchant = db.get(Merchant, merchant_id)
    if merchant is None:
        raise HTTPException(status_code=404, detail="Merchant is not seeded")
    records = db.query(Transaction).filter(Transaction.merchant_id == merchant.id)
    if from_date:
        records = records.filter(Transaction.transaction_date >= from_date)
    if to_date:
        records = records.filter(Transaction.transaction_date <= to_date)
    return records.order_by(Transaction.transaction_date, Transaction.id).all()


@router.get("/me")
def merchant_me(identity: dict = Depends(require_merchant), db: Session = Depends(get_db)) -> dict:
    merchant = get_demo_merchant(db, identity)
    return response({
            "merchant": {
                "id": merchant.id,
                "name": merchant.name,
                "business_type": merchant.business_type,
                "city": merchant.city,
                "consented_at": merchant.consented_at.isoformat(),
                "preferred_language": merchant.preferred_language,
                "scenario": merchant.scenario,
            },
            "data_as_of": effective_as_of(db).isoformat(),
        })


@router.get("/transactions")
def merchant_transactions(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    db: Session = Depends(get_db),
    identity: dict = Depends(require_merchant),
) -> dict:
    records = get_demo_records(db, from_date, to_date) if identity.get("anonymous") else get_demo_records(db, from_date, to_date, identity["merchant_id"])
    return response({
            "records": [
                {
                    "id": item.id,
                    "date": item.transaction_date.isoformat(),
                    "direction": item.direction,
                    "category": item.category,
                    "amount": decimal(item.amount),
                    "description": item.description,
                }
                for item in records
            ],
            "count": len(records),
            "data_quality": {"invalid_rows_stored": 0, "note": "Invalid input rows are skipped during seeding."},
            "data_as_of": effective_as_of(db).isoformat(),
        })


@router.get("/summary")
def merchant_summary(identity: dict = Depends(require_merchant), db: Session = Depends(get_db)) -> dict:
    records = get_demo_records(db) if identity.get("anonymous") else get_demo_records(db, merchant_id=identity["merchant_id"])
    summary = monthly_summary(records)
    return response({**summary, "data_as_of": effective_as_of(db).isoformat()})


@router.get("/forecast")
def merchant_forecast(identity: dict = Depends(require_merchant), db: Session = Depends(get_db)) -> dict:
    records = get_demo_records(db) if identity.get("anonymous") else get_demo_records(db, merchant_id=identity["merchant_id"])
    return response({**forecast_transactions(records, horizon_days=30, prefer_prophet=settings.use_prophet).as_dict(), "data_as_of": effective_as_of(db).isoformat()})


def get_merchant_consent(db: Session, merchant_id: int) -> Consent:
    consent = db.query(Consent).filter(Consent.merchant_id == merchant_id).order_by(Consent.id.desc()).first()
    if consent is None:
        raise HTTPException(status_code=404, detail="Consent record is not seeded")
    return consent


@router.get("/consent")
def merchant_consent(identity: dict = Depends(require_merchant), db: Session = Depends(get_db), lang: str | None = Query(default=None)) -> dict:
    merchant = get_demo_merchant(db, identity)
    consent = get_merchant_consent(db, merchant.id)
    return response(
        {
            "consent": {
                "scope": consent.scope,
                "status": consent.status,
                "granted_at": consent.granted_at.isoformat(),
                "expires_at": consent.expires_at.isoformat() if consent.expires_at else None,
                "revoked_at": consent.revoked_at.isoformat() if consent.revoked_at else None,
                "message_key": "consent.transaction_history",
                "params": {},
                "text": t("consent.transaction_history", lang if lang in {"en", "hi", "bn"} else merchant.preferred_language),
            },
            "data_as_of": effective_as_of(db).isoformat(),
        })


@router.post("/consent/revoke")
def revoke_consent(identity: dict = Depends(require_merchant), db: Session = Depends(get_db), lang: str | None = Query(default=None)) -> dict:
    merchant = get_demo_merchant(db, identity)
    consent = get_merchant_consent(db, identity.get("merchant_id", DEMO_MERCHANT_ID))
    consent.status = "revoked"
    consent.revoked_at = datetime.utcnow()
    loan = db.query(Loan).filter(Loan.merchant_id == consent.merchant_id).first()
    if loan:
        audit = create_audit_record(
            db,
            loan_id=loan.id,
            record_type="consent_change",
            record={"merchant_id": consent.merchant_id, "scope": consent.scope, "status": consent.status, "changed_by": "merchant"},
            rule_version="cashira-consent-v1",
        )
        anchor_audit_record(db, audit)
    else:
        audit = None
    db.commit()
    selected_lang = lang if lang in {"en", "hi", "bn"} else merchant.preferred_language
    return response({"consent": {"status": consent.status, "scope": consent.scope}, "message_key": "consent.revoked", "params": {}, "message": t("consent.revoked", selected_lang), "audit_record_id": audit.id if audit else None, **record_info(audit)})


@router.get("/messages")
def merchant_messages(identity: dict = Depends(require_merchant), db: Session = Depends(get_db), lang: str | None = Query(default=None)) -> dict:
    merchant = get_demo_merchant(db, identity)
    selected_lang = lang if lang in {"en", "hi", "bn"} else merchant.preferred_language
    actions = db.query(LenderAction).filter(LenderAction.merchant_id == merchant.id, LenderAction.action_type == "reminder").order_by(LenderAction.id.desc()).all()
    return response({"data_as_of": effective_as_of(db).isoformat(), "messages": [{"id": item.id, "message_key": item.message_key, "params": json.loads(item.message_params_json), "text": t(item.message_key or "reminders.contact", selected_lang, **json.loads(item.message_params_json)), "language": selected_lang, "date": item.created_at.isoformat()} for item in actions]})
