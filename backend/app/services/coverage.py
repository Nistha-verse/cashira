"""Data coverage and daily sales metrics used in plain-language reasons."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from statistics import mean, pstdev
from typing import Any

from ..config import settings


def row_date(row: Any) -> date:
    value = row.get("transaction_date") if isinstance(row, dict) else row.transaction_date
    return value if isinstance(value, date) else date.fromisoformat(str(value)[:10])


def row_value(row: Any, key: str) -> Any:
    return row.get(key) if isinstance(row, dict) else getattr(row, key)


def data_coverage(rows: list[Any], as_of: date, window_days: int = 30) -> dict[str, Any]:
    start = as_of - timedelta(days=window_days - 1)
    covered = {row_date(row) for row in rows if start <= row_date(row) <= as_of}
    ratio = len(covered) / window_days if window_days else 0.0
    return {
        "covered_days": len(covered),
        "window_days": window_days,
        "coverage_ratio": round(ratio, 4),
        "coverage_percent": round(ratio * 100, 1),
        "caveat": ratio < settings.data_coverage_min,
    }


def daily_sales_cv(rows: list[Any], as_of: date, window_days: int = 28) -> float:
    start = as_of - timedelta(days=window_days - 1)
    daily: dict[date, float] = defaultdict(float)
    for row in rows:
        try:
            row_day = row_date(row)
            if start <= row_day <= as_of and row_value(row, "direction") == "inflow":
                daily[row_day] += float(row_value(row, "amount"))
        except (AttributeError, TypeError, ValueError):
            continue
    values = [daily.get(start + timedelta(days=index), 0.0) for index in range(window_days)]
    average = mean(values) if values else 0.0
    return round(pstdev(values) / average, 4) if average else 0.0
