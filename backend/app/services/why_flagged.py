"""Plain-language evidence behind a lender priority tier."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from statistics import mean
from typing import Any

from ..i18n import t
from .coverage import data_coverage, row_date, row_value
from .priority import days_until_due
from .signals import render_signal_reason


def _rendered(key: str, params: dict[str, Any]) -> dict[str, str]:
    return {language: t(key, language, **params) for language in ("en", "hi", "bn")}


def _item(key: str, params: dict[str, Any]) -> dict[str, Any]:
    texts = _rendered(key, params)
    return {"message_key": key, "params": params, "text": texts, "texts": texts}


def _sales_windows(rows: list[Any], as_of: date) -> tuple[float, float, float, int]:
    daily: dict[date, float] = defaultdict(float)
    for row in rows:
        try:
            if row_value(row, "direction") == "inflow":
                daily[row_date(row)] += float(row_value(row, "amount"))
        except (AttributeError, TypeError, ValueError):
            continue
    recent_days = [as_of - timedelta(days=index) for index in range(13, -1, -1)]
    prior_days = [as_of - timedelta(days=index) for index in range(27, 13, -1)]
    recent = sum(daily.get(day, 0.0) for day in recent_days)
    prior = sum(daily.get(day, 0.0) for day in prior_days)
    change = ((recent - prior) / prior * 100) if prior else 0.0
    usual: dict[int, list[float]] = defaultdict(list)
    baseline_start = as_of - timedelta(days=69)
    baseline_end = as_of - timedelta(days=14)
    current = baseline_start
    while current <= baseline_end:
        usual[current.weekday()].append(daily.get(current, 0.0))
        current += timedelta(days=1)
    below = sum(1 for day in recent_days if usual[day.weekday()] and daily.get(day, 0.0) < mean(usual[day.weekday()]))
    return recent, prior, round(change, 1), below


def build_why_flagged(rows: list[Any], evaluation: dict[str, Any], loan, as_of: date) -> list[dict[str, Any]]:
    reasons: list[dict[str, Any]] = []
    for signal in evaluation["signals"]["signals"]:
        if signal["severity"] == "none":
            continue
        localized = {language: render_signal_reason(signal, language)["text"] for language in ("en", "hi", "bn")}
        reasons.append({"message_key": signal["reason_key"], "params": signal["params"], "text": localized, "texts": localized, "signal_id": signal["id"], "severity": signal["severity"], "rule_version": signal["rule_version"]})

    recent, prior, change, below = _sales_windows(rows, as_of)
    reasons.append(_item("reasons.sales_14", {"recent_sales": round(recent, 2), "previous_sales": round(prior, 2), "change": change}))
    reasons.append(_item("reasons.below_usual", {"below_days": below, "total_days": 14}))
    due_days = days_until_due(loan, as_of)
    reasons.append(_item("reasons.due_days", {"days": due_days if due_days is not None else 0}))
    coverage = evaluation["data_coverage"]
    caveat = " Data may be incomplete." if coverage["caveat"] else ""
    reasons.append(_item("reasons.coverage", {"covered_days": coverage["covered_days"], "window_days": coverage["window_days"], "coverage_percent": coverage["coverage_percent"], "caveat": caveat}))
    return reasons
