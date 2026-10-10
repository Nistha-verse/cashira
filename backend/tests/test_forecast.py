from datetime import date, timedelta

from app.services.forecast import BaselineForecaster, forecast_transactions


def rows(days=70):
    start = date(2024, 1, 1)
    return [
        {"transaction_date": start + timedelta(days=i), "direction": "inflow", "category": "sales", "amount": 100 + (i % 7) * 10}
        for i in range(days)
    ]


def test_baseline_returns_thirty_daily_values_and_range():
    result = BaselineForecaster().forecast(rows())
    assert result.method == "baseline"
    assert len(result.daily) == 30
    assert result.lower_net <= result.expected_net <= result.upper_net


def test_forecast_falls_back_when_prophet_fails(monkeypatch):
    def fail(self, rows, horizon_days=30):
        raise RuntimeError("simulated Prophet failure")

    monkeypatch.setattr("app.services.forecast.ProphetForecaster.forecast", fail)
    result = forecast_transactions(rows(), prefer_prophet=True)
    assert result.method == "baseline"


def test_empty_forecast_is_deterministic():
    first = BaselineForecaster().forecast([]).as_dict()
    second = BaselineForecaster().forecast([]).as_dict()
    assert first == second
