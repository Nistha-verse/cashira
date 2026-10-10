from decimal import Decimal

from app.services.loan_state import apply_payment, calculate_standard_emi


def test_standard_emi_and_shortfall_are_monthly():
    emi = calculate_standard_emi(120000, 12, 12)
    assert emi > Decimal("10000")
    state = {"current_balance": Decimal("120000"), "annual_rate": Decimal("12"), "standard_emi": emi, "carried_shortfall": 0}
    applied = apply_payment(state, Decimal("5000"))
    assert applied["interest_component"] == Decimal("1200.00")
    assert applied["principal_component"] == Decimal("3800.00")
    assert applied["carried_shortfall_after"] == emi - Decimal("5000")
    assert applied["balance_after"] == Decimal("116200.00")
