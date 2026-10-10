"""Monthly inflow/outflow/net cash-flow aggregation."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from statistics import mean
from typing import Any


def monthly_summary(rows: list[Any]) -> dict[str, Any]:
    grouped: dict[str, dict[str, float]] = defaultdict(lambda: {"inflow": 0.0, "outflow": 0.0})
    for row in rows:
        try:
            value = row.get("transaction_date") if isinstance(row, dict) else row.transaction_date
            row_date = value if isinstance(value, date) else date.fromisoformat(str(value)[:10])
            direction = row.get("direction") if isinstance(row, dict) else row.direction
            amount = float(row.get("amount") if isinstance(row, dict) else row.amount)
            if direction in {"inflow", "outflow"} and amount >= 0:
                grouped[row_date.strftime("%Y-%m")][direction] += amount
        except (TypeError, ValueError, AttributeError):
            continue
    months = []
    for month in sorted(grouped):
        values = grouped[month]
        inflow = round(values["inflow"], 2)
        outflow = round(values["outflow"], 2)
        months.append({"month": month, "inflow": inflow, "outflow": outflow, "net": round(inflow - outflow, 2)})
    nets = [item["net"] for item in months]
    trailing = mean(nets[:-1][-3:]) if len(nets) > 1 else None
    for item in months:
        prior = [m["net"] for m in months if m["month"] < item["month"]][-3:]
        item["change_vs_trailing_average"] = (
            round(item["net"] - mean(prior), 2) if prior else None
        )
    return {
        "months": months,
        "latest_month": months[-1] if months else None,
        "trailing_average_net": round(trailing, 2) if trailing is not None else None,
        "valid": bool(months),
    }
