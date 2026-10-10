from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Loan, Payment, Recommendation, Transaction
from ..schemas import PaymentRequest
from ..services.engine import recommend_emi
from ..services.explain import explain_recommendation
from ..services.forecast import forecast_transactions
from ..services.loan_state import apply_payment
from ..services.summary import monthly_summary
from ..services.audit import create_audit_record
from ..config import settings
from .helpers import assumptions, decimal, iso_datetime, response
from .merchant import DEMO_MERCHANT_ID

router = APIRouter(prefix="/loan", tags=["loan"])


def get_demo_loan(db: Session) -> Loan:
    loan = db.query(Loan).filter(Loan.merchant_id == DEMO_MERCHANT_ID).first()
    if loan is None:
        raise HTTPException(status_code=404, detail="Demo loan is not seeded")
    return loan


def loan_payload(loan: Loan) -> dict:
    return {
        "id": loan.id,
        "principal": decimal(loan.principal),
        "annual_rate_percent": decimal(loan.annual_rate),
        "tenure_months": loan.tenure_months,
        "min_emi": decimal(loan.min_emi),
        "max_emi": decimal(loan.max_emi),
        "standard_emi": decimal(loan.standard_emi),
        "due_day": loan.due_day,
        "current_balance": decimal(loan.current_balance),
        "carried_forward_shortfall": decimal(loan.carried_shortfall),
        "payments": [
            {
                "id": payment.id,
                "amount": decimal(payment.amount),
                "payment_date": payment.payment_date.isoformat(),
                "balance_after": decimal(payment.balance_after),
                "carried_forward_shortfall": decimal(payment.carried_shortfall_after),
            }
            for payment in loan.payments
        ],
        **assumptions(),
    }


def calculate_recommendation(db: Session, loan: Loan) -> tuple[dict, dict, dict]:
    records = db.query(Transaction).filter(Transaction.merchant_id == DEMO_MERCHANT_ID).all()
    summary = monthly_summary(records)
    forecast = forecast_transactions(records, horizon_days=30, prefer_prophet=settings.use_prophet)
    result = recommend_emi(summary, forecast.as_dict(), loan)
    result["explanation"] = explain_recommendation(result["reasons"])
    result["forecast_method"] = forecast.method
    return result, summary, forecast.as_dict()


@router.get("")
def loan_details(db: Session = Depends(get_db)) -> dict:
    return response({"loan": loan_payload(get_demo_loan(db))})


@router.get("/recommendation")
def loan_recommendation(db: Session = Depends(get_db)) -> dict:
    loan = get_demo_loan(db)
    result, summary, forecast = calculate_recommendation(db, loan)
    recommendation = Recommendation(
        loan_id=loan.id,
        emi=result["emi"],
        reasons_json=json.dumps(result["reasons"], sort_keys=True),
        explanation=result["explanation"],
        forecast_method=result["forecast_method"],
        rule_version=result["rule_version"],
    )
    db.add(recommendation)
    db.flush()
    audit = create_audit_record(
        db,
        loan_id=loan.id,
        record_type="recommendation",
        record={
            "record_type": "recommendation",
            "recommendation_id": recommendation.id,
            "loan_ref": str(loan.id),
            "emi": result["emi"],
            "reasons": result["reasons"],
            "forecast_method": result["forecast_method"],
            "rule_version": result["rule_version"],
        },
        rule_version=result["rule_version"],
    )
    db.commit()
    db.refresh(recommendation)
    return response(
        {
            "recommendation_id": recommendation.id,
            "current_emi": decimal(result["emi"]),
            "range": {"min": decimal(loan.min_emi), "max": decimal(loan.max_emi)},
            "standard_emi": decimal(loan.standard_emi),
            "reasons": result["reasons"],
            "explanation": result["explanation"],
            "forecast_method": result["forecast_method"],
            "rule_version": result["rule_version"],
            "audit_record_id": audit.id,
            "forecast": {"expected_net": forecast["expected_net"], "lower_net": forecast["lower_net"], "upper_net": forecast["upper_net"]},
            "summary": {"trailing_average_net": summary["trailing_average_net"], "latest_month": summary["latest_month"]},
            **assumptions(),
        }
    )


@router.post("/pay")
def loan_pay(payload: PaymentRequest, db: Session = Depends(get_db)) -> dict:
    loan = get_demo_loan(db)
    recommendation, _, _ = calculate_recommendation(db, loan)
    amount = payload.amount if payload.amount is not None else recommendation["emi"]
    if amount < loan.min_emi or amount > loan.max_emi:
        raise HTTPException(status_code=422, detail="Payment amount must stay within the configured monthly EMI range")
    state = {
        "current_balance": loan.current_balance,
        "annual_rate": loan.annual_rate,
        "standard_emi": loan.standard_emi,
        "carried_shortfall": loan.carried_shortfall,
    }
    applied = apply_payment(state, amount, payload.payment_date or date.today())
    loan.current_balance = applied["balance_after"]
    loan.carried_shortfall = applied["carried_shortfall_after"]
    payment = Payment(
        loan_id=loan.id,
        amount=applied["amount"],
        payment_date=applied["payment_date"],
        interest_component=applied["interest_component"],
        principal_component=applied["principal_component"],
        balance_after=applied["balance_after"],
        carried_shortfall_after=applied["carried_shortfall_after"],
    )
    db.add(payment)
    db.flush()
    audit = create_audit_record(
        db,
        loan_id=loan.id,
        record_type="payment",
        record={
            "record_type": "payment",
            "payment_id": payment.id,
            "loan_ref": str(loan.id),
            "amount": payment.amount,
            "payment_date": payment.payment_date.isoformat(),
            "interest_component": payment.interest_component,
            "principal_component": payment.principal_component,
            "balance_after": payment.balance_after,
            "carried_forward_shortfall": payment.carried_shortfall_after,
            "rule_version": "cashira-emi-v1",
        },
        rule_version="cashira-emi-v1",
    )
    db.commit()
    db.refresh(payment)
    return response(
        {
            "payment_id": payment.id,
            "audit_record_id": audit.id,
            "payment": {
                "amount": decimal(payment.amount),
                "payment_date": payment.payment_date.isoformat(),
                "interest_component": decimal(payment.interest_component),
                "principal_component": decimal(payment.principal_component),
                "balance_after": decimal(payment.balance_after),
                "carried_forward_shortfall": decimal(payment.carried_shortfall_after),
            },
            "message": "Simulated monthly payment recorded.",
            **assumptions(),
        }
    )
