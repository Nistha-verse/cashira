"""Deterministic portfolio priority tiers for lender review."""

from __future__ import annotations

from datetime import date

from ..config import settings

PRIORITY_RANK = {"high": 0, "medium": 1, "healthy": 2, "consent withdrawn": 3}


def next_due_date(loan, as_of: date) -> date | None:
    if loan is None:
        return None
    year, month = as_of.year, as_of.month
    if as_of.day >= loan.due_day:
        month += 1
        if month == 13:
            month, year = 1, year + 1
    return date(year, month, min(loan.due_day, 28))


def days_until_due(loan, as_of: date) -> int | None:
    due = next_due_date(loan, as_of)
    return (due - as_of).days if due else None


def priority_for(status: str, due_days: int | None) -> str:
    if status == "red":
        return "high"
    if status == "amber":
        if due_days is not None and due_days <= settings.priority_due_days:
            return "high"
        return "medium"
    return "healthy"
