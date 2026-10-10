"""Create the reproducible synthetic Cashira demo dataset.

Run from ``backend/`` with ``python -m scripts.seed``. The command replaces
the demo tables, so running it repeatedly produces the same valid database.
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete

from app.db import SessionLocal, init_db
from app.models import AuditRecord, Loan, Merchant, Payment, Recommendation, Transaction
from app.services.loan_state import calculate_standard_emi
from app.services.validation import validate_rows


MERCHANTS = [
    {"id": 1, "name": "Riya's Corner Store", "phone": "+919900000001", "city": "Bengaluru", "base": 34000.0, "cost": 0.66},
    {"id": 2, "name": "Asha Daily Needs", "phone": "+919900000002", "city": "Pune", "base": 29500.0, "cost": 0.69},
    {"id": 3, "name": "Kabir General Mart", "phone": "+919900000003", "city": "Jaipur", "base": 38500.0, "cost": 0.64},
]


def generate_synthetic_rows(seed: int = 42) -> list[dict]:
    """Generate daily inflows and outflows plus deliberate bad input rows."""

    rng = random.Random(seed)
    start = date(2024, 1, 1)
    rows: list[dict] = []
    for merchant in MERCHANTS:
        current = start
        while current.year == 2024:
            weekday_factor = 1.18 if current.weekday() >= 5 else 0.96
            month_start_factor = 1.17 if current.day <= 5 else 1.0
            festival_factor = 1.0
            if current.month == 10 and 24 <= current.day <= 31:
                festival_factor = 1.52
            if current.month == 11 and current.day <= 3:
                festival_factor = 1.25
            weak_factor = 0.52 if merchant["id"] == 1 and current.month == 6 else 1.0
            base = merchant["base"] * weekday_factor * month_start_factor * festival_factor * weak_factor
            inflow = max(100.0, rng.gauss(base, base * 0.08))
            rows.append(
                {
                    "merchant_key": merchant["id"],
                    "transaction_date": current.isoformat(),
                    "direction": "inflow",
                    "category": "shop sales",
                    "amount": round(inflow, 2),
                    "description": "Synthetic daily shop sales",
                }
            )
            inventory = max(50.0, rng.gauss(inflow * merchant["cost"], inflow * 0.035))
            rows.append(
                {
                    "merchant_key": merchant["id"],
                    "transaction_date": current.isoformat(),
                    "direction": "outflow",
                    "category": "inventory purchases",
                    "amount": round(inventory, 2),
                    "description": "Synthetic supplier inventory purchase",
                }
            )
            if current.day == 1:
                rows.append(
                    {
                        "merchant_key": merchant["id"],
                        "transaction_date": current.isoformat(),
                        "direction": "outflow",
                        "category": "rent",
                        "amount": round(9000 + merchant["id"] * 650, 2),
                        "description": "Synthetic monthly rent",
                    }
                )
            if current.day in {10, 20}:
                rows.append(
                    {
                        "merchant_key": merchant["id"],
                        "transaction_date": current.isoformat(),
                        "direction": "outflow",
                        "category": "supplier payments",
                        "amount": round(2500 + merchant["id"] * 275, 2),
                        "description": "Synthetic supplier payment",
                    }
                )
            current += timedelta(days=1)

    # These rows are intentionally never inserted; seed reports that the validator skipped them.
    rows.extend(
        [
            {"merchant_key": 1, "transaction_date": "2024-02-01", "direction": "inflow", "category": "shop sales", "amount": -10},
            {"merchant_key": 1, "transaction_date": None, "direction": "outflow", "category": "inventory purchases", "amount": 100},
            {"merchant_key": 1, "transaction_date": "2024-02-02", "direction": "other", "category": "unknown", "amount": 100},
        ]
    )
    # Duplicate a real key deliberately; the validator will count and skip it.
    rows.append(dict(rows[0]))
    return rows


def seed_database(seed: int = 42) -> dict[str, int]:
    init_db()
    rows = generate_synthetic_rows(seed)
    db = SessionLocal()
    try:
        for model in (AuditRecord, Recommendation, Payment, Loan, Transaction, Merchant):
            db.execute(delete(model))
        db.commit()
        merchants = {}
        for item in MERCHANTS:
            merchant = Merchant(
                id=item["id"],
                name=item["name"],
                phone=item["phone"],
                city=item["city"],
                consented_at=datetime(2024, 1, 1),
            )
            db.add(merchant)
            merchants[item["id"]] = merchant
        db.flush()
        valid_count = 0
        rejected_count = 0
        for merchant in MERCHANTS:
            merchant_rows = [row for row in rows if row.get("merchant_key") == merchant["id"]]
            result = validate_rows(merchant_rows)
            valid_count += result.report.accepted_rows
            rejected_count += result.report.rejected_rows
            for row in result.valid_rows:
                db.add(
                    Transaction(
                        merchant_id=merchant["id"],
                        transaction_date=row["transaction_date"],
                        direction=row["direction"],
                        category=row["category"],
                        amount=row["amount"],
                        description=row["description"],
                    )
                )
            principal = Decimal("300000") + Decimal(merchant["id"] * 50000)
            standard = calculate_standard_emi(principal, Decimal("18"), 24)
            db.add(
                Loan(
                    merchant_id=merchant["id"],
                    principal=principal,
                    annual_rate=Decimal("18.00"),
                    tenure_months=24,
                    min_emi=standard * Decimal("0.60"),
                    max_emi=standard * Decimal("1.45"),
                    standard_emi=standard,
                    due_day=5,
                    current_balance=principal,
                    carried_shortfall=Decimal("0.00"),
                )
            )
        db.commit()
        return {"merchants": len(MERCHANTS), "valid_rows": valid_count, "rejected_rows": rejected_count}
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the Cashira synthetic demo database")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    result = seed_database(args.seed)
    print(f"Seeded {result['merchants']} merchants and {result['valid_rows']} valid records; skipped {result['rejected_rows']} invalid rows.")


if __name__ == "__main__":
    main()
