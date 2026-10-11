from datetime import date, timedelta

from app.services.weekly import weekly_cash_flow


def test_only_complete_monday_sunday_weeks_are_used():
    start = date(2026, 9, 7)
    rows = [
        {"transaction_date": start + timedelta(days=i), "direction": "inflow", "amount": 100}
        for i in range(24)
    ]
    result = weekly_cash_flow(rows, date(2026, 9, 30), weeks=3)
    assert result["complete_through"] == "2026-09-27"
    assert [week["week_start"] for week in result["weeks"]] == ["2026-09-07", "2026-09-14", "2026-09-21"]
    assert all(week["sales"] == 700 for week in result["weeks"])
    assert result["days_since_last_transaction"] == 0
