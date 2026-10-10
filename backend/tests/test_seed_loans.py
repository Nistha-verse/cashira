from decimal import Decimal

from app.services.loan_state import calculate_standard_emi
from scripts.seed import DEMO_PRINCIPALS


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
