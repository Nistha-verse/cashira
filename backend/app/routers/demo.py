"""Demo-only controls for app walkthroughs."""

from __future__ import annotations

import random
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..authz import identity_from_request
from ..config import settings
from ..db import get_db
from ..models import Merchant, Transaction
from ..schemas import SimulateWeekRequest
from ..services.alerts import evaluate_merchant_alerts
from ..services.audit import create_audit_record
from .helpers import response

router = APIRouter(prefix="/demo", tags=["demo"])


def require_demo(request: Request) -> None:
    identity = identity_from_request(request)
    demo_header = request.headers.get("x-demo-token", "").lower()
    if not settings.demo_mode and demo_header != "demo" and not (identity and identity.get("role") in {"lender", "demo"}):
        raise HTTPException(status_code=403, detail="Demo controls require DEMO_MODE=true, a demo token, or a lender session")


@router.post("/simulate-week")
def simulate_week(payload: SimulateWeekRequest, _: None = Depends(require_demo), db: Session = Depends(get_db)) -> dict:
    if payload.pattern not in {"decline", "stable", "recover"}:
        raise HTTPException(status_code=422, detail="Pattern must be decline, stable, or recover")
    merchant = db.get(Merchant, payload.merchant_id)
    if merchant is None:
        raise HTTPException(status_code=404, detail="Merchant is not seeded")
    latest = db.query(Transaction).filter(Transaction.merchant_id == merchant.id).order_by(Transaction.transaction_date.desc()).first()
    if latest is None:
        raise HTTPException(status_code=404, detail="Merchant has no transaction history")
    previous = db.query(Transaction).filter(Transaction.merchant_id == merchant.id, Transaction.transaction_date >= latest.transaction_date - timedelta(days=28), Transaction.direction == "inflow").all()
    typical = sum(float(row.amount) for row in previous) / max(1, len(previous))
    multiplier = {"decline": 0.65, "stable": 1.0, "recover": 1.25}[payload.pattern]
    rng = random.Random(f"cashira-demo:{merchant.id}:{latest.transaction_date}:{payload.pattern}")
    for offset in range(1, 8):
        transaction_date = latest.transaction_date + timedelta(days=offset)
        sales = round(max(100.0, rng.gauss(typical * multiplier, typical * 0.03)), 2)
        db.add(Transaction(merchant_id=merchant.id, transaction_date=transaction_date, direction="inflow", category="shop sales", amount=sales, description=f"Demo simulated {payload.pattern} week sales"))
        db.add(Transaction(merchant_id=merchant.id, transaction_date=transaction_date, direction="outflow", category="inventory purchases", amount=round(sales * 0.8, 2), description="Demo simulated inventory purchase"))
    db.flush()
    evaluation = evaluate_merchant_alerts(db, merchant, latest.transaction_date + timedelta(days=7))
    loan = merchant.loans[0] if merchant.loans else None
    audit = create_audit_record(db, loan_id=loan.id, record_type="demo_simulation", record={"merchant_id": merchant.id, "pattern": payload.pattern, "start_date": (latest.transaction_date + timedelta(days=1)).isoformat()}, rule_version="cashira-demo-v1") if loan else None
    db.commit()
    return response({"demo_only": True, "merchant_id": merchant.id, "pattern": payload.pattern, "transactions_added": 14, "status": evaluation["evaluation"]["signals"]["status"], "audit_record_id": audit.id if audit else None})


@router.post("/reset")
def reset_demo(_: None = Depends(require_demo)) -> dict:
    from scripts.seed import seed_database

    result = seed_database(42)
    return response({"demo_only": True, "reset": True, "seed": result})
