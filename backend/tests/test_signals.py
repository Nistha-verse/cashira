from app.services.signals import evaluate_signals, signal_s1, signal_s2, signal_s3, signal_s4, signal_s5, signal_s6


def weekly_fixture(sales, days=0):
    weeks = [{"sales": value, "inflow": value, "outflow": 50, "net": value - 50} for value in sales]
    return {
        "weeks": weeks,
        "consecutive_weekly_declines": sum(1 for i in range(len(sales) - 1, 0, -1) if sales[i] < sales[i - 1]),
        "trailing_8_week_baseline": {"sales": 100, "inflow": 100, "outflow": 50, "net": 50},
        "last_2_week_average_sales": sum(sales[-2:]) / 2,
        "last_2_week_inflow": sum(sales[-2:]),
        "last_2_week_outflow": 100,
        "four_week_net_monthly_equivalent": 100,
        "days_since_last_transaction": days,
    }


def test_s1_thresholds_are_inclusive_for_drop_and_decline_count():
    amber = signal_s1(weekly_fixture([100] * 8 + [100, 96, 93, 90]))
    assert amber["severity"] == "amber"
    red = signal_s1(weekly_fixture([100, 100, 90, 80, 75, 74, 73, 72, 71, 70]))
    assert red["severity"] == "red"


def test_signal_boundary_rules():
    assert signal_s2({**weekly_fixture([100] * 10), "last_2_week_average_sales": 80})["severity"] == "none"
    assert signal_s2({**weekly_fixture([100] * 10), "last_2_week_average_sales": 79.99})["severity"] == "amber"
    assert signal_s3({**weekly_fixture([100] * 10), "four_week_net_monthly_equivalent": 200}, {"standard_emi": 100})["severity"] == "none"
    assert signal_s3({**weekly_fixture([100] * 10), "four_week_net_monthly_equivalent": 129}, {"standard_emi": 100})["severity"] == "red"
    assert signal_s4({**weekly_fixture([100] * 10), "days_since_last_transaction": 3})["severity"] == "amber"
    assert signal_s4({**weekly_fixture([100] * 10), "days_since_last_transaction": 7})["severity"] == "red"
    assert signal_s5({**weekly_fixture([100] * 10), "last_2_week_outflow": 130})["severity"] == "none"
    assert signal_s6({"late_recent": True, "overdue": False})["severity"] == "amber"
    assert signal_s6({"late_recent": True, "overdue": True})["severity"] == "red"


def test_overall_status_and_attention_order():
    result = evaluate_signals(
        {**weekly_fixture([100, 95, 90, 80]), "consecutive_weekly_declines": 3, "days_since_last_transaction": 8, "four_week_net_monthly_equivalent": 300},
        {"standard_emi": 100},
        {"overdue": True},
    )
    assert result["status"] == "red"
    assert result["what_to_look_at_first"][0] in {"S1", "S4", "S6"}
