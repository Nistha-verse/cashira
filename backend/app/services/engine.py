"""Pure, deterministic EMI recommendation rule."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

RULE_VERSION = "cashira-emi-v1"
MONEY = Decimal("0.01")


def _money(value: Any) -> Decimal:
    return Decimal(str(value)).quantize(MONEY, rounding=ROUND_HALF_UP)


def _clamp(value: Decimal, low: Decimal, high: Decimal) -> Decimal:
    return max(low, min(high, value))


def _loan_value(loan: Any, field: str) -> Any:
    if isinstance(loan, dict):
        return loan.get(field)
    return getattr(loan, field, None)


def recommend_emi(summary: dict[str, Any], forecast: dict[str, Any], loan: Any) -> dict[str, Any]:
    """Scale between configured bounds from forecast/trailing-net ratio.

    Ratios at or below 0.60 select the minimum and ratios at or above 1.40
    select the maximum. The forecast informs the position but never chooses a
    repayment amount outside the pre-agreed loan range.
    """

    minimum = _money(_loan_value(loan, "min_emi"))
    maximum = _money(_loan_value(loan, "max_emi"))
    standard = _money(_loan_value(loan, "standard_emi"))
    minimum, maximum = min(minimum, maximum), max(minimum, maximum)
    reasons: list[dict[str, Any]] = []
    trailing = summary.get("trailing_average_net") if isinstance(summary, dict) else None
    expected = forecast.get("expected_net") if isinstance(forecast, dict) else None
    valid = bool(summary.get("valid")) and trailing is not None and expected is not None
    try:
        trailing_decimal = _money(trailing)
        expected_decimal = _money(expected)
        valid = valid and trailing_decimal > 0 and expected_decimal.is_finite()
    except Exception:
        valid = False
    if not valid:
        reasons.append(
            {
                "code": "missing_or_invalid_data",
                "message": "Some cash-flow data is missing or invalid, so the standard monthly EMI is used.",
            }
        )
        emi = _clamp(standard, minimum, maximum)
    else:
        ratio = expected_decimal / trailing_decimal
        position = max(Decimal("0"), min(Decimal("1"), (ratio - Decimal("0.60")) / Decimal("0.80")))
        emi = _clamp(minimum + (maximum - minimum) * position, minimum, maximum).quantize(
            MONEY, rounding=ROUND_HALF_UP
        )
        reasons.append(
            {
                "code": "cash_flow_position",
                "message": "The recommended EMI reflects the forecast next-month net cash flow compared with the trailing average.",
                "forecast_net": float(expected_decimal),
                "trailing_average_net": float(trailing_decimal),
                "ratio": float(round(ratio, 4)),
            }
        )
        if ratio < Decimal("0.90"):
            reasons.append({"code": "lower_capacity", "message": "Recent cash flow suggests keeping the monthly payment closer to the lower end of the agreed range."})
        elif ratio > Decimal("1.10"):
            reasons.append({"code": "higher_capacity", "message": "Recent cash flow suggests capacity for a monthly payment nearer the upper end of the agreed range."})
        else:
            reasons.append({"code": "steady_capacity", "message": "Recent cash flow is close to its trailing average."})
    return {"emi": emi, "reasons": reasons, "rule_version": RULE_VERSION}
