"""Small shared HTTP helpers."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from ..config import AMORTIZATION_NOTICE, PROTOTYPE_NOTICE


def response(payload: dict[str, Any]) -> dict[str, Any]:
    return {"prototype": True, "notice": PROTOTYPE_NOTICE, **payload}


def decimal(value: Decimal | float | int | None) -> float | None:
    return None if value is None else round(float(value), 2)


def iso_datetime(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def assumptions() -> dict[str, str]:
    return {"amortization": AMORTIZATION_NOTICE, "repayment_frequency": "monthly"}
