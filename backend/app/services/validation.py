"""Safe validation for imported synthetic transaction rows."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any


@dataclass(frozen=True)
class DataQualityReport:
    input_rows: int
    accepted_rows: int
    rejected_rows: int
    invalid_amounts: int
    invalid_dates: int
    invalid_directions: int
    duplicates: int
    gaps: int

    def as_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationResult:
    valid_rows: list[dict[str, Any]]
    report: DataQualityReport


def _parse_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def validate_rows(rows: Iterable[dict[str, Any]] | None) -> ValidationResult:
    """Validate rows without throwing for malformed or missing fields."""

    valid: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    invalid_amounts = invalid_dates = invalid_directions = duplicates = 0
    input_rows = 0
    dates: set[date] = set()

    for raw in rows or []:
        input_rows += 1
        if not isinstance(raw, dict):
            invalid_dates += 1
            continue
        parsed_date = _parse_date(raw.get("transaction_date", raw.get("date")))
        if parsed_date is None:
            invalid_dates += 1
            continue
        try:
            amount = Decimal(str(raw.get("amount")))
            if not amount.is_finite() or amount <= 0:
                raise InvalidOperation
            amount = amount.quantize(Decimal("0.01"))
        except (InvalidOperation, TypeError, ValueError):
            invalid_amounts += 1
            continue
        direction = str(raw.get("direction", "")).lower()
        if direction not in {"inflow", "outflow"}:
            invalid_directions += 1
            continue
        category = str(raw.get("category") or "uncategorized")
        key = (parsed_date, direction, category, amount)
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        dates.add(parsed_date)
        valid.append(
            {
                "transaction_date": parsed_date,
                "direction": direction,
                "category": category,
                "amount": amount,
                "description": str(raw.get("description") or "Synthetic record"),
            }
        )

    gaps = 0
    if len(dates) > 1:
        current, last = min(dates), max(dates)
        while current <= last:
            if current not in dates:
                gaps += 1
            current += timedelta(days=1)
    rejected = input_rows - len(valid)
    return ValidationResult(
        valid_rows=valid,
        report=DataQualityReport(
            input_rows=input_rows,
            accepted_rows=len(valid),
            rejected_rows=rejected,
            invalid_amounts=invalid_amounts,
            invalid_dates=invalid_dates,
            invalid_directions=invalid_directions,
            duplicates=duplicates,
            gaps=gaps,
        ),
    )
