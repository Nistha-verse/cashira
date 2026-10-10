"""Daily net-inflow forecasting with a deterministic baseline fallback."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from decimal import Decimal
from statistics import mean, pstdev
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class ForecastResult:
    method: str
    horizon_days: int
    expected_net: float
    lower_net: float
    upper_net: float
    daily: list[dict[str, Any]]
    disclaimer: str = "Forecast is an estimate, not a guarantee."

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _row_date(row: Any) -> date:
    value = row.get("transaction_date") if isinstance(row, dict) else row.transaction_date
    return value if isinstance(value, date) else date.fromisoformat(str(value)[:10])


def _row_net(row: Any) -> float:
    direction = row.get("direction") if isinstance(row, dict) else row.direction
    amount = row.get("amount") if isinstance(row, dict) else row.amount
    value = float(amount)
    return value if direction == "inflow" else -value


def _daily_series(rows: list[Any]) -> dict[date, float]:
    result: dict[date, float] = defaultdict(float)
    for row in rows:
        try:
            result[_row_date(row)] += _row_net(row)
        except (TypeError, ValueError, AttributeError):
            continue
    return dict(result)


class Forecaster(ABC):
    name: str

    @abstractmethod
    def forecast(self, rows: list[Any], horizon_days: int = 30) -> ForecastResult:
        raise NotImplementedError


class BaselineForecaster(Forecaster):
    """Trailing eight-week same-weekday average with a bounded seasonal factor."""

    name = "baseline"

    def forecast(self, rows: list[Any], horizon_days: int = 30) -> ForecastResult:
        series = _daily_series(rows)
        if not series:
            # A fixed anchor keeps an empty-input result deterministic.
            empty_anchor = date(2024, 1, 1)
            daily = [
                {"date": (empty_anchor + timedelta(days=i + 1)).isoformat(), "expected": 0.0, "lower": 0.0, "upper": 0.0}
                for i in range(horizon_days)
            ]
            return ForecastResult(self.name, horizon_days, 0.0, 0.0, 0.0, daily)
        last_date = max(series)
        start = last_date - timedelta(days=55)
        values = [series.get(start + timedelta(days=i), 0.0) for i in range(56)]
        recent = values[-28:]
        prior = values[:28]
        recent_mean = mean(recent) if recent else 0.0
        prior_mean = mean(prior) if prior else 0.0
        seasonal_factor = 1.0 if abs(prior_mean) < 0.01 else max(0.8, min(1.2, recent_mean / prior_mean))
        weekday_values: dict[int, list[float]] = defaultdict(list)
        for offset, value in enumerate(values):
            weekday_values[(start + timedelta(days=offset)).weekday()].append(value)
        overall = mean(values) if values else 0.0
        spread = pstdev(values) if len(values) > 1 else abs(overall) * 0.1
        daily: list[dict[str, Any]] = []
        for i in range(1, horizon_days + 1):
            future_date = last_date + timedelta(days=i)
            same_weekday = weekday_values.get(future_date.weekday(), values)
            expected = mean(same_weekday) * seasonal_factor if same_weekday else overall
            interval = max(spread * 1.28, abs(expected) * 0.08, 1.0)
            daily.append(
                {
                    "date": future_date.isoformat(),
                    "expected": round(expected, 2),
                    "lower": round(expected - interval, 2),
                    "upper": round(expected + interval, 2),
                }
            )
        return ForecastResult(
            self.name,
            horizon_days,
            round(sum(item["expected"] for item in daily), 2),
            round(sum(item["lower"] for item in daily), 2),
            round(sum(item["upper"] for item in daily), 2),
            daily,
        )


class ProphetForecaster(Forecaster):
    name = "prophet"

    def forecast(self, rows: list[Any], horizon_days: int = 30) -> ForecastResult:
        series = _daily_series(rows)
        if len(series) < 60:
            raise ValueError("Prophet requires at least 60 observed days")
        try:
            from prophet import Prophet
        except Exception as exc:  # pragma: no cover - environment dependent
            raise RuntimeError("Prophet is unavailable") from exc
        first, last = min(series), max(series)
        dates = pd.date_range(first, last, freq="D")
        frame = pd.DataFrame({"ds": dates, "y": [series.get(day.date(), 0.0) for day in dates]})
        model = Prophet(daily_seasonality=False, weekly_seasonality=True, yearly_seasonality=True)
        model.fit(frame)
        future = model.make_future_dataframe(periods=horizon_days, freq="D", include_history=False)
        prediction = model.predict(future)
        daily = [
            {
                "date": row.ds.date().isoformat(),
                "expected": round(float(row.yhat), 2),
                "lower": round(float(row.yhat_lower), 2),
                "upper": round(float(row.yhat_upper), 2),
            }
            for row in prediction.itertuples()
        ]
        return ForecastResult(
            self.name,
            horizon_days,
            round(sum(item["expected"] for item in daily), 2),
            round(sum(item["lower"] for item in daily), 2),
            round(sum(item["upper"] for item in daily), 2),
            daily,
        )


def forecast_transactions(
    rows: list[Any], horizon_days: int = 30, prefer_prophet: bool = True
) -> ForecastResult:
    """Use Prophet when possible, recording baseline whenever it falls back."""

    if prefer_prophet:
        try:
            return ProphetForecaster().forecast(rows, horizon_days)
        except Exception:
            pass
    return BaselineForecaster().forecast(rows, horizon_days)
