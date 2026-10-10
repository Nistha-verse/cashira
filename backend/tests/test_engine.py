from decimal import Decimal

from app.services.engine import RULE_VERSION, recommend_emi


LOAN = {"min_emi": Decimal("1000"), "max_emi": Decimal("3000"), "standard_emi": Decimal("2000")}


def test_weak_cash_flow_is_near_minimum_and_strong_is_near_maximum():
    weak = recommend_emi({"valid": True, "trailing_average_net": 10000}, {"expected_net": 6000}, LOAN)
    strong = recommend_emi({"valid": True, "trailing_average_net": 10000}, {"expected_net": 14000}, LOAN)
    assert weak["emi"] == Decimal("1000.00")
    assert strong["emi"] == Decimal("3000.00")


def test_engine_is_deterministic_and_clamped():
    summary = {"valid": True, "trailing_average_net": 10000}
    forecast = {"expected_net": 10000}
    first = recommend_emi(summary, forecast, LOAN)
    second = recommend_emi(summary, forecast, LOAN)
    assert first == second
    assert first["rule_version"] == RULE_VERSION
    assert Decimal("1000") <= first["emi"] <= Decimal("3000")


def test_missing_data_uses_standard_emi_with_reason():
    result = recommend_emi({"valid": False, "trailing_average_net": None}, {}, LOAN)
    assert result["emi"] == Decimal("2000.00")
    assert result["reasons"][0]["code"] == "missing_or_invalid_data"
