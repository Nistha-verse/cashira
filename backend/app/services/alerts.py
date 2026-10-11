"""Database orchestration for idempotent alert evaluation."""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from ..config import settings
from ..models import Alert, Consent, Loan, Merchant, Payment, Transaction
from .signals import evaluate_signals
from .weekly import weekly_cash_flow
from .coverage import daily_sales_cv, data_coverage


def effective_as_of(db: Session, as_of: date | None = None) -> date:
    if as_of:
        return as_of
    if settings.demo_as_of:
        try:
            return date.fromisoformat(settings.demo_as_of)
        except ValueError:
            pass
    latest = db.query(Transaction.transaction_date).order_by(Transaction.transaction_date.desc()).first()
    return latest[0] if latest else date.today()


def consent_is_active(consent: Consent | None, as_of: date) -> bool:
    if consent is None or consent.status != "active" or consent.revoked_at is not None:
        return False
    return consent.expires_at is None or consent.expires_at.date() >= as_of


def repayment_summary(payments: list[Payment], as_of: date) -> dict[str, Any]:
    late_recent = any(
        payment.status == "late"
        and payment.due_date is not None
        and (as_of - payment.due_date).days <= 92
        and payment.due_date <= as_of
        for payment in payments
    )
    overdue = any(payment.status in {"overdue", "missed"} and payment.due_date and payment.due_date <= as_of for payment in payments)
    latest = sorted(payments, key=lambda item: item.due_date or date.min)[-1] if payments else None
    return {
        "late_recent": late_recent,
        "overdue": overdue,
        "latest_status": latest.status if latest else "none",
        "latest_due_date": latest.due_date.isoformat() if latest and latest.due_date else None,
        "days_overdue": max(0, (as_of - latest.due_date).days) if latest and latest.status in {"overdue", "missed"} and latest.due_date else 0,
    }


def merchant_signal_evaluation(db: Session, merchant: Merchant, as_of: date | None = None) -> dict[str, Any]:
    effective = effective_as_of(db, as_of)
    rows = db.query(Transaction).filter(Transaction.merchant_id == merchant.id, Transaction.transaction_date <= effective).all()
    weekly = weekly_cash_flow(rows, effective)
    summary_rows = db.query(Payment).join(Loan).filter(Loan.merchant_id == merchant.id).all()
    loan = db.query(Loan).filter(Loan.merchant_id == merchant.id).first()
    loan_dict = {"standard_emi": float(loan.standard_emi)} if loan else None
    repayment = repayment_summary(summary_rows, effective)
    coverage = data_coverage(rows, effective)
    volatility = daily_sales_cv(rows, effective)
    signals = evaluate_signals(weekly, loan_dict, repayment, volatility)
    return {"as_of": effective, "weekly": weekly, "signals": signals, "repayment": repayment, "loan": loan, "data_coverage": coverage, "daily_sales_cv": volatility}


def evaluate_merchant_alerts(db: Session, merchant: Merchant, as_of: date | None = None) -> dict[str, Any]:
    evaluated = merchant_signal_evaluation(db, merchant, as_of)
    weekly = evaluated["weekly"]
    week_key = weekly["weeks"][-1]["week_key"] if weekly.get("weeks") else evaluated["as_of"].isoformat()
    created = []
    for signal in evaluated["signals"]["signals"]:
        if signal["severity"] == "none":
            continue
        existing = db.query(Alert).filter(
            Alert.merchant_id == merchant.id,
            Alert.signal_id == signal["id"],
            Alert.week_key == week_key,
        ).first()
        if existing:
            created.append(existing)
            continue
        alert = Alert(
            merchant_id=merchant.id,
            signal_id=signal["id"],
            severity=signal["severity"],
            week_key=week_key,
            status="new",
            message_key=f"alerts.{signal['id'].lower()}",
            params_json=json.dumps(signal["params"], sort_keys=True),
            rule_version=signal["rule_version"],
        )
        db.add(alert)
        created.append(alert)
    db.flush()
    return {"merchant_id": merchant.id, "as_of": evaluated["as_of"], "evaluation": evaluated, "alerts": created}
