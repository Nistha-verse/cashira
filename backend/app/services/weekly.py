"""Monday-to-Sunday cash-flow aggregation for lender review."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from statistics import mean
from typing import Any


def _date(row: Any) -> date:
    value = row.get("transaction_date") if isinstance(row, dict) else row.transaction_date
    return value if isinstance(value, date) else date.fromisoformat(str(value)[:10])


def _amount(row: Any) -> float:
    value = row.get("amount") if isinstance(row, dict) else row.amount
    return float(value)


def _direction(row: Any) -> str:
    return row.get("direction") if isinstance(row, dict) else row.direction


def _week_start(value: date) -> date:
    return value - timedelta(days=value.weekday())


def weekly_cash_flow(rows: list[Any], as_of: date | None = None, weeks: int = 26) -> dict[str, Any]:
    """Return complete Monday-Sunday weeks ending no later than ``as_of``."""

    parsed_dates = [_date(row) for row in rows if row is not None]
    effective_as_of = as_of or (max(parsed_dates) if parsed_dates else date(2024, 1, 1))
    complete_end = effective_as_of - timedelta(days=(effective_as_of.weekday() + 1) % 7)
    first_end = complete_end - timedelta(days=(weeks - 1) * 7)
    grouped: dict[date, dict[str, float]] = defaultdict(lambda: {"inflow": 0.0, "outflow": 0.0})
    latest_transaction: date | None = None
    for row in rows:
        try:
            row_date = _date(row)
            if row_date > effective_as_of:
                continue
            latest_transaction = max(latest_transaction or row_date, row_date)
            week_start = _week_start(row_date)
            if first_end - timedelta(days=6) <= week_start <= complete_end - timedelta(days=6):
                direction = _direction(row)
                if direction in {"inflow", "outflow"}:
                    grouped[week_start][direction] += _amount(row)
        except (AttributeError, TypeError, ValueError):
            continue

    output: list[dict[str, Any]] = []
    for index in range(weeks):
        # ``complete_end`` is a Sunday; use the corresponding Monday.
        start = complete_end - timedelta(days=(weeks - 1 - index) * 7 + 6)
        values = grouped[start]
        inflow = round(values["inflow"], 2)
        outflow = round(values["outflow"], 2)
        net = round(inflow - outflow, 2)
        output.append(
            {
                "week_key": f"{start.isoformat()}_{(start + timedelta(days=6)).isoformat()}",
                "week_start": start.isoformat(),
                "week_end": (start + timedelta(days=6)).isoformat(),
                "inflow": inflow,
                "outflow": outflow,
                "sales": inflow,
                "net": net,
                "week_over_week_change": None,
            }
        )
    for index in range(1, len(output)):
        previous = output[index - 1]["sales"]
        output[index]["week_over_week_change"] = (
            round((output[index]["sales"] - previous) / previous, 4) if previous else None
        )

    # Compare the recent two weeks against the eight preceding complete weeks.
    last_8 = output[-10:-2]
    last_2 = output[-2:]
    last_4 = output[-4:]
    baseline = {
        "sales": round(mean(item["sales"] for item in last_8), 2) if last_8 else 0.0,
        "inflow": round(mean(item["inflow"] for item in last_8), 2) if last_8 else 0.0,
        "outflow": round(mean(item["outflow"] for item in last_8), 2) if last_8 else 0.0,
        "net": round(mean(item["net"] for item in last_8), 2) if last_8 else 0.0,
    }
    consecutive_declines = 0
    for index in range(len(output) - 1, 0, -1):
        if output[index]["sales"] < output[index - 1]["sales"]:
            consecutive_declines += 1
        else:
            break
    last_four_net = round(sum(item["net"] for item in last_4), 2)
    last_two_sales = mean(item["sales"] for item in last_2) if last_2 else 0.0
    prior_four_sales = sum(item["sales"] for item in output[-8:-4]) if len(output) >= 8 else 0.0
    recent_four_sales = sum(item["sales"] for item in output[-4:])
    return {
        "as_of": effective_as_of.isoformat(),
        "complete_through": complete_end.isoformat(),
        "weeks": output,
        "trailing_8_week_baseline": baseline,
        "last_2_week_average_sales": round(last_two_sales, 2),
        "last_2_week_outflow": round(sum(item["outflow"] for item in last_2), 2),
        "last_2_week_inflow": round(sum(item["inflow"] for item in last_2), 2),
        "last_4_week_net": last_four_net,
        "four_week_net_monthly_equivalent": round(last_four_net * 13 / 12, 2),
        "four_week_sales_change": round((recent_four_sales - prior_four_sales) / prior_four_sales, 4) if prior_four_sales else None,
        "consecutive_weekly_declines": consecutive_declines,
        "latest_transaction_date": latest_transaction.isoformat() if latest_transaction else None,
        "days_since_last_transaction": (effective_as_of - latest_transaction).days if latest_transaction else None,
    }
