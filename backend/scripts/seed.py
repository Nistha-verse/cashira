"""Create the reproducible synthetic Cashira demo dataset.

Run from ``backend/`` with ``python -m scripts.seed``. The command replaces
the demo tables, so running it repeatedly produces the same valid database.
"""

from __future__ import annotations

import argparse
import calendar
import os
import random
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete

from app.db import SessionLocal, init_db
from app.config import BASE_DIR, settings
from app.models import (
    Alert,
    AuditRecord,
    Consent,
    Lender,
    LenderAction,
    LenderPortfolio,
    Loan,
    Merchant,
    Payment,
    Recommendation,
    Transaction,
)
from app.services.loan_state import apply_payment, calculate_standard_emi
from app.services.summary import monthly_summary
from app.services.validation import validate_rows
from app.services.weekly import weekly_cash_flow
from app.services.alerts import merchant_signal_evaluation, effective_as_of
from app.services.priority import days_until_due, priority_for


MERCHANTS = [
    {"id": 1, "name": "Riya's Corner Store", "phone": "+919900000001", "city": "Bengaluru", "scale": 1.00, "rent": 9000.0, "preferred_language": "hi", "scenario": "weak September"},
    {"id": 2, "name": "Asha Daily Needs", "phone": "+919900000002", "city": "Pune", "scale": 0.93, "rent": 8500.0, "preferred_language": "en", "scenario": "stable"},
    {"id": 3, "name": "Kabir General Mart", "phone": "+919900000003", "city": "Jaipur", "scale": 1.07, "rent": 9500.0, "preferred_language": "hi", "scenario": "stable"},
    {"id": 4, "name": "Mitali Kirana", "phone": "+919900000004", "city": "Kolkata", "scale": 0.96, "rent": 8800.0, "preferred_language": "bn", "scenario": "volatile sales"},
    {"id": 5, "name": "Howrah Daily Store", "phone": "+919900000005", "city": "Howrah", "scale": 1.02, "rent": 9200.0, "preferred_language": "bn", "scenario": "stable"},
    {"id": 6, "name": "Siliguri Bazaar", "phone": "+919900000006", "city": "Siliguri", "scale": 0.90, "rent": 8200.0, "preferred_language": "bn", "scenario": "stable"},
    {"id": 7, "name": "Durgapur Needs", "phone": "+919900000007", "city": "Durgapur", "scale": 1.05, "rent": 9400.0, "preferred_language": "bn", "scenario": "growing"},
    {"id": 8, "name": "Lucknow Basket", "phone": "+919900000008", "city": "Lucknow", "scale": 0.98, "rent": 9000.0, "preferred_language": "hi", "scenario": "falling for three weeks"},
    {"id": 9, "name": "Patna Family Mart", "phone": "+919900000009", "city": "Patna", "scale": 1.01, "rent": 9000.0, "preferred_language": "hi", "scenario": "steady sales decline"},
    {"id": 10, "name": "Jaipur Fresh Corner", "phone": "+919900000010", "city": "Jaipur", "scale": 1.04, "rent": 9300.0, "preferred_language": "hi", "scenario": "recovering after dip"},
    {"id": 11, "name": "Delhi Neighbour Store", "phone": "+919900000011", "city": "Delhi", "scale": 0.94, "rent": 8600.0, "preferred_language": "hi", "scenario": "data gap"},
    {"id": 12, "name": "Noida Daily Mart", "phone": "+919900000012", "city": "Noida", "scale": 1.03, "rent": 9400.0, "preferred_language": "en", "scenario": "revoked consent"},
]

DATA_END = date.fromisoformat(os.getenv("SEED_END_DATE", "2026-09-30"))
_start_month_index = DATA_END.year * 12 + DATA_END.month - 1 - 23
DATA_START = date(_start_month_index // 12, _start_month_index % 12 + 1, 1)
RIYA_WEAK_MONTH = (2026, 9)

# Demo loan sizing is explicit so the seeded story stays stable when merchant
# transaction assumptions evolve. Standard EMI is still derived by the shared
# fixed-rate amortization formula below.
DEMO_PRINCIPALS = {
    1: Decimal("180000"),  # Riya
    2: Decimal("200000"),  # Asha
    3: Decimal("220000"),  # Kabir
    4: Decimal("190000"),
    5: Decimal("200000"),
    6: Decimal("180000"),
    7: Decimal("210000"),
    8: Decimal("190000"),
    9: Decimal("200000"),
    10: Decimal("210000"),
    11: Decimal("180000"),
    12: Decimal("200000"),
}


def _scenario_factor(merchant: dict, current: date) -> float:
    """Return a deterministic sales trend factor for new demo scenarios."""

    if merchant["id"] <= 3:
        return 1.0
    days_from_end = (DATA_END - current).days
    if merchant["scenario"] == "growing":
        return 1.0 + max(0, 56 - days_from_end) / 56 * 0.18
    if merchant["scenario"] in {"falling for three weeks", "steady sales decline"}:
        if days_from_end < 28:
            week = min(3, (27 - days_from_end) // 7)
            # Chronological factors are about .94, .77, .60, .43. This keeps
            # the decline visible even through the final-week festival lift.
            return 0.94 - week * 0.17
        return 1.0
    if merchant["scenario"] == "recovering after dip":
        if 28 <= days_from_end < 70:
            return 0.72
        if days_from_end < 28:
            return 0.72 + (28 - days_from_end) / 28 * 0.28
    if merchant["scenario"] == "volatile sales":
        return 0.58 if current.toordinal() % 14 < 7 else 1.34
    return 1.0


def _month_due_date(year: int, month: int, due_day: int = 5) -> date:
    return date(year, month, min(due_day, calendar.monthrange(year, month)[1]))


def _previous_months(end_date: date, count: int) -> list[tuple[int, int]]:
    result = []
    year, month = end_date.year, end_date.month
    for _ in range(count):
        result.append((year, month))
        month -= 1
        if month == 0:
            year -= 1
            month = 12
    return list(reversed(result))


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
            if merchant["id"] == 11 and current > DATA_END - timedelta(days=8):
                current += timedelta(days=1)
                continue
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
            base = (
                sales_base
                * merchant["scale"]
                * month_start_factor
                * festival_factor
                * weak_factor
                * _scenario_factor(merchant, current)
            )
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
    database_url = settings.database_url
    expected = (BASE_DIR / "data" / "cashira.db").resolve()
    test_database = (BASE_DIR / "data" / "test_cashira.db").resolve()
    if not database_url.startswith("sqlite:///"):
        raise RuntimeError("Refusing to seed a non-demo database path")
    database_path = Path(database_url.removeprefix("sqlite:///")).resolve()
    if database_path not in {expected, test_database}:
        raise RuntimeError("Refusing to seed a non-demo database path")
    init_db()
    rows = generate_synthetic_rows(seed)
    db = SessionLocal()
    try:
        for model in (
            AuditRecord,
            LenderAction,
            Alert,
            Consent,
            LenderPortfolio,
            Lender,
            Recommendation,
            Payment,
            Loan,
            Transaction,
            Merchant,
        ):
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
                preferred_language=item["preferred_language"],
                scenario=item["scenario"],
            )
            db.add(merchant)
            merchants[item["id"]] = merchant
        db.flush()
        lender = Lender(name="Demo Lender (simulated)", phone=os.getenv("LENDER_DEMO_PHONE", "+919900000099"))
        db.add(lender)
        db.flush()
        valid_count = 0
        rejected_count = 0
        loans: dict[int, Loan] = {}
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
            loan = Loan(
                    merchant_id=merchant["id"],
                    principal=principal,
                    annual_rate=Decimal("18.00"),
                    tenure_months=24,
                    min_emi=standard * Decimal("0.70"),
                    max_emi=standard * Decimal("1.20"),
                    standard_emi=standard,
                    due_day=20 if merchant["id"] == 4 else 5,
                    current_balance=principal,
                    carried_shortfall=Decimal("0.00"),
                )
            db.add(loan)
            loans[merchant["id"]] = loan
            db.add(LenderPortfolio(lender_id=lender.id, merchant_id=merchant["id"]))
            revoked = merchant["id"] == 12
            db.add(
                Consent(
                    merchant_id=merchant["id"],
                    scope="transaction history",
                    granted_at=datetime.combine(DATA_START, datetime.min.time()),
                    expires_at=datetime.combine(DATA_END + timedelta(days=365), datetime.min.time()),
                    revoked_at=datetime.combine(DATA_END, datetime.min.time()) if revoked else None,
                    status="revoked" if revoked else "active",
                )
            )
        db.flush()
        # Six historical monthly payment events keep the demo balance tied to
        # its payment history. Merchant 8 is late in both final months;
        # merchant 9 has one missed/overdue final-month event.
        payment_months = _previous_months(DATA_END, 6)
        for merchant in MERCHANTS:
            loan = loans[merchant["id"]]
            state = {
                "current_balance": loan.current_balance,
                "annual_rate": loan.annual_rate,
                "standard_emi": loan.standard_emi,
                "carried_shortfall": loan.carried_shortfall,
            }
            for index, (year, month) in enumerate(payment_months):
                due_date = _month_due_date(year, month, loan.due_day)
                missed = merchant["id"] == 9 and index == len(payment_months) - 1
                late_days = (8 + index % 3) if merchant["id"] == 8 and index >= len(payment_months) - 2 else 0
                if missed:
                    db.add(
                        Payment(
                            loan_id=loan.id,
                            amount=Decimal("0.00"),
                            # The legacy schema requires a date. Status carries
                            # the fact that no payment was made for this due date.
                            payment_date=due_date,
                            due_date=due_date,
                            interest_component=Decimal("0.00"),
                            principal_component=Decimal("0.00"),
                            balance_after=state["current_balance"],
                            carried_shortfall_after=state["carried_shortfall"],
                            status="overdue",
                            days_late=max(0, (DATA_END - due_date).days),
                        )
                    )
                    continue
                paid_date = due_date + timedelta(days=late_days)
                applied = apply_payment(state, loan.standard_emi, paid_date)
                state["current_balance"] = applied["balance_after"]
                state["carried_shortfall"] = applied["carried_shortfall_after"]
                db.add(
                    Payment(
                        loan_id=loan.id,
                        amount=applied["amount"],
                        payment_date=paid_date,
                        due_date=due_date,
                        interest_component=applied["interest_component"],
                        principal_component=applied["principal_component"],
                        balance_after=applied["balance_after"],
                        carried_shortfall_after=applied["carried_shortfall_after"],
                        status="late" if late_days else "paid",
                        days_late=late_days,
                    )
                )
            loan.current_balance = state["current_balance"]
            loan.carried_shortfall = state["carried_shortfall"]
        db.commit()
        return {"merchants": len(MERCHANTS), "valid_rows": valid_count, "rejected_rows": rejected_count, "lender_id": lender.id}
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
        print("\nMerchant scenario summary")
        print(f"{'Merchant':<24} {'Scenario':<24} {'Priority':<18} {'Signals':<18} {'Due':<8} {'Coverage':<12}")
        print("-" * 150)
        for merchant in MERCHANTS:
            records = db.query(Transaction).filter(Transaction.merchant_id == merchant["id"]).all()
            effective = effective_as_of(db)
            evaluation = merchant_signal_evaluation(db, db.get(Merchant, merchant["id"]), effective)
            loan = db.query(Loan).filter(Loan.merchant_id == merchant["id"]).first()
            consent = db.query(Consent).filter(Consent.merchant_id == merchant["id"]).first()
            active_signals = ",".join(item["id"] for item in evaluation["signals"]["signals"] if item["severity"] != "none") or "none"
            due = days_until_due(loan, effective)
            priority = "consent withdrawn" if consent and consent.status != "active" else priority_for(evaluation["signals"]["status"], due)
            coverage = evaluation["data_coverage"]
            print(f"{merchant['name']:<24} {merchant['scenario']:<24} {priority:<18} {active_signals:<18} {str(due):<8} {coverage['covered_days']}/{coverage['window_days']}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
