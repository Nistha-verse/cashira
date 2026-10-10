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
from app.services.summary import monthly_summary
from app.services.validation import validate_rows


MERCHANTS = [
    {"id": 1, "name": "Riya's Corner Store", "phone": "+919900000001", "city": "Bengaluru", "scale": 1.00, "rent": 9000.0},
    {"id": 2, "name": "Asha Daily Needs", "phone": "+919900000002", "city": "Pune", "scale": 0.93, "rent": 8500.0},
    {"id": 3, "name": "Kabir General Mart", "phone": "+919900000003", "city": "Jaipur", "scale": 1.07, "rent": 9500.0},
]

DATA_START = date(2024, 10, 1)
DATA_END = date(2026, 9, 30)
RIYA_WEAK_MONTH = (2026, 9)

# Demo loan sizing is explicit so the seeded story stays stable when merchant
# transaction assumptions evolve. Standard EMI is still derived by the shared
# fixed-rate amortization formula below.
DEMO_PRINCIPALS = {
    1: Decimal("180000"),  # Riya
    2: Decimal("200000"),  # Asha
    3: Decimal("220000"),  # Kabir
}


def generate_synthetic_rows(seed: int = 42) -> list[dict]:
    """Generate 24 months of daily inflows/outflows plus four bad rows.

    The first three sales bases are deliberately visible in the code: roughly
    ₹7,000 on weekdays, ₹12,000 on Saturdays, and ₹8,500 on Sundays before
    month-start, festival, merchant-scale, and weak-month effects.
    """

    rng = random.Random(seed)
    rows: list[dict] = []
    for merchant in MERCHANTS:
        current = DATA_START
        while current <= DATA_END:
            if current.weekday() < 5:
                sales_base = 7000.0
            elif current.weekday() == 5:
                sales_base = 12000.0
            else:
                sales_base = 8500.0
            month_start_factor = 1.12 if current.day <= 5 else 1.0
            # Diwali peaks are represented in every year covered by this fixed
            # demo window.  September 2026 is the lead-up because the window
            # ends at the last full month before the current demo date.
            festival_factor = 1.0
            if (current.year in {2024, 2025} and current.month == 10 and current.day >= 15) or (
                current.year == 2026 and current.month == 9 and current.day >= 20
            ):
                festival_factor = 1.30
            # The late-September festival lift offsets part of the reduction,
            # so 0.55 yields an observed 35-40% sales drop for the full month.
            weak_factor = 0.55 if merchant["id"] == 1 and (current.year, current.month) == RIYA_WEAK_MONTH else 1.0
            base = sales_base * merchant["scale"] * month_start_factor * festival_factor * weak_factor
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
            inventory = max(50.0, rng.gauss(inflow * 0.80, inflow * 0.025))
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
                        "amount": round(merchant["rent"], 2),
                        "description": "Synthetic monthly rent",
                    }
                )
            if current.day == 20:
                rows.append(
                    {
                        "merchant_key": merchant["id"],
                        "transaction_date": current.isoformat(),
                        "direction": "outflow",
                        "category": "supplier payments",
                        "amount": round(rng.uniform(2000.0, 4000.0), 2),
                        "description": "Synthetic supplier payment",
                    }
                )
            current += timedelta(days=1)

    # These rows are intentionally never inserted; seed reports that the validator skipped them.
    rows.extend(
        [
            {"merchant_key": 1, "transaction_date": "2025-02-01", "direction": "inflow", "category": "shop sales", "amount": -10},
            {"merchant_key": 1, "transaction_date": None, "direction": "outflow", "category": "inventory purchases", "amount": 100},
            {"merchant_key": 1, "transaction_date": "2025-02-02", "direction": "other", "category": "unknown", "amount": 100},
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
                consented_at=datetime.combine(DATA_START, datetime.min.time()),
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
            principal = DEMO_PRINCIPALS[merchant["id"]]
            standard = calculate_standard_emi(principal, Decimal("18"), 24)
            db.add(
                Loan(
                    merchant_id=merchant["id"],
                    principal=principal,
                    annual_rate=Decimal("18.00"),
                    tenure_months=24,
                    min_emi=standard * Decimal("0.70"),
                    max_emi=standard * Decimal("1.20"),
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
    db = SessionLocal()
    try:
        print("\nMerchant monthly cash-flow table")
        print(f"{'Merchant':<24} {'Month':<8} {'Inflow':>12} {'Outflow':>12} {'Net':>12}")
        print("-" * 72)
        for merchant in MERCHANTS:
            records = db.query(Transaction).filter(Transaction.merchant_id == merchant["id"]).all()
            summary = monthly_summary(records)
            for month in summary["months"]:
                print(
                    f"{merchant['name']:<24} {month['month']:<8} "
                    f"₹{month['inflow']:>10,.2f} ₹{month['outflow']:>10,.2f} ₹{month['net']:>10,.2f}"
                )
    finally:
        db.close()


if __name__ == "__main__":
    main()
