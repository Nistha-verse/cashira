from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Merchant, Transaction
from ..services.forecast import forecast_transactions
from ..services.summary import monthly_summary
from ..config import settings
from .helpers import decimal, response

router = APIRouter(prefix="/merchant", tags=["merchant"])
DEMO_MERCHANT_ID = 1


def get_demo_merchant(db: Session) -> Merchant:
    merchant = db.get(Merchant, DEMO_MERCHANT_ID)
    if merchant is None:
        raise HTTPException(status_code=404, detail="Demo merchant is not seeded")
    return merchant


def get_demo_records(db: Session, from_date: date | None = None, to_date: date | None = None) -> list[Transaction]:
    merchant = get_demo_merchant(db)
    records = db.query(Transaction).filter(Transaction.merchant_id == merchant.id)
    if from_date:
        records = records.filter(Transaction.transaction_date >= from_date)
    if to_date:
        records = records.filter(Transaction.transaction_date <= to_date)
    return records.order_by(Transaction.transaction_date, Transaction.id).all()


@router.get("/me")
def merchant_me(db: Session = Depends(get_db)) -> dict:
    merchant = get_demo_merchant(db)
    return response(
        {
            "merchant": {
                "id": merchant.id,
                "name": merchant.name,
                "business_type": merchant.business_type,
                "city": merchant.city,
                "consented_at": merchant.consented_at.isoformat(),
            }
        }
    )


@router.get("/transactions")
def merchant_transactions(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    db: Session = Depends(get_db),
) -> dict:
    records = get_demo_records(db, from_date, to_date)
    return response(
        {
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
        }
    )


@router.get("/summary")
def merchant_summary(db: Session = Depends(get_db)) -> dict:
    records = get_demo_records(db)
    summary = monthly_summary(records)
    return response(summary)


@router.get("/forecast")
def merchant_forecast(db: Session = Depends(get_db)) -> dict:
    records = get_demo_records(db)
    return response(forecast_transactions(records, horizon_days=30, prefer_prophet=settings.use_prophet).as_dict())
