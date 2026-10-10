"""Prototype fixed-rate monthly amortization and simulated payment state."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

MONEY = Decimal("0.01")


def money(value: Any) -> Decimal:
    return Decimal(str(value)).quantize(MONEY, rounding=ROUND_HALF_UP)


def calculate_standard_emi(principal: Any, annual_rate: Any, tenure_months: int) -> Decimal:
    principal = money(principal)
    months = int(tenure_months)
    monthly_rate = Decimal(str(annual_rate)) / Decimal("1200")
    if months <= 0:
        raise ValueError("tenure_months must be positive")
    if monthly_rate == 0:
        return (principal / months).quantize(MONEY, rounding=ROUND_HALF_UP)
    factor = (Decimal("1") + monthly_rate) ** months
    return (principal * monthly_rate * factor / (factor - Decimal("1"))).quantize(MONEY, rounding=ROUND_HALF_UP)


def apply_payment(state: dict[str, Any], amount: Any, payment_date: date | None = None) -> dict[str, Any]:
    """Apply one monthly simulated payment and return the new state.

    Interest is calculated once per payment event. There is no daily deduction.
    """

    amount = money(amount)
    if amount <= 0:
        raise ValueError("payment amount must be positive")
    balance_before = money(state["current_balance"])
    annual_rate = Decimal(str(state["annual_rate"]))
    standard = money(state["standard_emi"])
    monthly_interest = (balance_before * annual_rate / Decimal("1200")).quantize(MONEY, rounding=ROUND_HALF_UP)
    interest_component = min(amount, monthly_interest)
    principal_component = min(max(amount - monthly_interest, Decimal("0")), balance_before)
    balance_after = max(Decimal("0"), balance_before - principal_component).quantize(MONEY)
    shortfall_before = money(state.get("carried_shortfall", 0))
    shortfall_after = (shortfall_before + max(Decimal("0"), standard - amount)).quantize(MONEY)
    return {
        "amount": amount,
        "payment_date": payment_date or date.today(),
        "interest_component": interest_component.quantize(MONEY),
        "principal_component": principal_component.quantize(MONEY),
        "balance_before": balance_before,
        "balance_after": balance_after,
        "carried_shortfall_after": shortfall_after,
    }
