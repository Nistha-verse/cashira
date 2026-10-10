from collections import defaultdict
from datetime import date
from decimal import Decimal
from statistics import mean

from app.services.loan_state import calculate_standard_emi
from app.services.summary import monthly_summary
from app.services.validation import validate_rows
from scripts.seed import DATA_END, DATA_START, DEMO_PRINCIPALS, MERCHANTS, RIYA_WEAK_MONTH, generate_synthetic_rows


def test_demo_principals_and_emi_ranges():
    expected = {
        1: Decimal("8986.34"),
        2: Decimal("9984.82"),
        3: Decimal("10983.30"),
    }
    for merchant_id, principal in DEMO_PRINCIPALS.items():
        standard = calculate_standard_emi(principal, Decimal("18"), 24)
        assert standard == expected[merchant_id]
        assert standard * Decimal("0.70") < standard < standard * Decimal("1.20")


def test_seeded_demo_loans_reset_state():
    from app.db import SessionLocal
    from app.models import Loan
    from scripts.seed import seed_database

    # The API smoke test exercises a payment, so explicitly verify that a
    # reseed restores the configured starting state.
    seed_database(42)
    db = SessionLocal()
    try:
        loans = {loan.merchant_id: loan for loan in db.query(Loan).all()}
        assert {1, 2, 3}.issubset(loans)
        for merchant_id, principal in DEMO_PRINCIPALS.items():
            loan = loans[merchant_id]
            standard = calculate_standard_emi(principal, Decimal("18"), 24)
            assert loan.principal == principal
            assert loan.current_balance == principal
            assert loan.carried_shortfall == Decimal("0.00")
            assert loan.standard_emi == standard
            assert loan.min_emi == (standard * Decimal("0.70")).quantize(Decimal("0.01"))
            assert loan.max_emi == (standard * Decimal("1.20")).quantize(Decimal("0.01"))
    finally:
        db.close()


def test_transaction_generator_profile_window_and_weak_month():
    rows = generate_synthetic_rows(42)
    assert rows == generate_synthetic_rows(42)

    valid_by_merchant = {}
    rejected = 0
    for merchant in MERCHANTS:
        result = validate_rows([row for row in rows if row.get("merchant_key") == merchant["id"]])
        rejected += result.report.rejected_rows
        valid_by_merchant[merchant["id"]] = result.valid_rows
    assert rejected == 4

    all_dates = [row["transaction_date"] for rows_for_merchant in valid_by_merchant.values() for row in rows_for_merchant]
    assert min(all_dates) == DATA_START
    assert max(all_dates) == DATA_END

    def is_peak(row_date: date) -> bool:
        return (row_date.year in {2024, 2025} and row_date.month == 10 and row_date.day >= 15) or (
            row_date.year == 2026 and row_date.month == 9 and row_date.day >= 20
        )

    riya_sales = [row for row in valid_by_merchant[1] if row["direction"] == "inflow"]
    base_sales = [
        row for row in riya_sales
        if row["transaction_date"].day > 5 and not is_peak(row["transaction_date"])
        and (row["transaction_date"].year, row["transaction_date"].month) != RIYA_WEAK_MONTH
    ]
    weekday_mean = mean(float(row["amount"]) for row in base_sales if row["transaction_date"].weekday() < 5)
    saturday_mean = mean(float(row["amount"]) for row in base_sales if row["transaction_date"].weekday() == 5)
    assert 6500 <= weekday_mean <= 7500
    assert 11000 <= saturday_mean <= 13000

    summaries = {}
    sales_by_month = {}
    for merchant_id, merchant_rows in valid_by_merchant.items():
        summaries[merchant_id] = monthly_summary(merchant_rows)
        sales_by_month[merchant_id] = defaultdict(float)
        for row in merchant_rows:
            if row["direction"] == "inflow":
                sales_by_month[merchant_id][row["transaction_date"].strftime("%Y-%m")] += float(row["amount"])

    normal_riya = [
        month for month in summaries[1]["months"]
        if month["month"] not in {"2024-10", "2025-10", "2026-09"}
    ]
    assert normal_riya
    assert all(30000 <= month["net"] <= 45000 for month in normal_riya)

    weak_sales = sales_by_month[1]["2026-09"]
    comparable_sales = sales_by_month[1]["2025-09"]
    assert 0.60 <= weak_sales / comparable_sales <= 0.65
    weak_month = next(month for month in summaries[1]["months"] if month["month"] == "2026-09")
    assert weak_month["net"] > float(calculate_standard_emi(180000, 18, 24) * Decimal("0.70"))
    assert weak_month["net"] < mean(month["net"] for month in normal_riya)

    normal_riya_sales = sum(sales_by_month[1][month["month"]] for month in normal_riya)
    for merchant_id in (2, 3):
        normal_sales = sum(sales_by_month[merchant_id][month["month"]] for month in normal_riya)
        assert 0.85 <= normal_sales / normal_riya_sales <= 1.15

    inventory = [row for row in valid_by_merchant[1] if row["category"] == "inventory purchases"]
    normal_inventory = sum(float(row["amount"]) for row in inventory if row["transaction_date"].strftime("%Y-%m") in {month["month"] for month in normal_riya})
    assert 0.77 <= normal_inventory / normal_riya_sales <= 0.83

    rent = [row for row in valid_by_merchant[1] if row["category"] == "rent"]
    assert len(rent) == 24
    assert all(8000 <= float(row["amount"]) <= 10000 for row in rent)
    assert float(next(row["amount"] for row in rent if row["transaction_date"].strftime("%Y-%m") == "2026-09")) == 9000

    supplier = [row for row in valid_by_merchant[1] if row["category"] == "supplier payments"]
    assert len(supplier) == 24
    assert all(2000 <= float(row["amount"]) <= 4000 for row in supplier)
