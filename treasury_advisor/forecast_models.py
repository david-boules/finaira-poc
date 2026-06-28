from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import BASE_DATE
from .forecast import net_cash_flow


MODEL_COLUMNS = [
    "customer_receipts",
    "other_inflows",
    "supplier_payments",
    "operating_expenses",
    "fx_payments",
]


@dataclass(frozen=True)
class ModelBacktest:
    model_name: str
    mae: float
    rmse: float
    bias: float
    reliability_score: float


@dataclass(frozen=True)
class StatisticalForecast:
    model_name: str
    frame: pd.DataFrame
    backtest: ModelBacktest
    component_models: dict[str, str]


def fit_statistical_forecast(df: pd.DataFrame, model: str = "exp_smoothing") -> StatisticalForecast:
    actuals = df[df["date"] < BASE_DATE].copy()
    future = df[(df["date"] >= BASE_DATE) & (df["date"] < BASE_DATE + pd.Timedelta(days=90))].copy()
    model = _resolve_model(model)
    backtest = backtest_model(actuals, model)

    forecast_frame = future[["date", "payroll", "debt_service", "capex", "ar_due", "ap_due", "currency_exposure"]].copy()
    component_models = {}
    for column in MODEL_COLUMNS:
        forecast_frame[column] = _forecast_component(actuals, future["date"], column, model)
        component_models[column] = _model_label(model)

    forecast_frame["net_cash_flow"] = net_cash_flow(forecast_frame)
    start_cash = float(actuals.iloc[-1]["closing_cash"])
    forecast_frame["statistical_projected_cash"] = start_cash + forecast_frame["net_cash_flow"].cumsum()
    return StatisticalForecast(
        model_name=_display_name(model),
        frame=forecast_frame,
        backtest=backtest,
        component_models=component_models,
    )


def backtest_model(actuals: pd.DataFrame, model: str = "exp_smoothing", holdout_days: int = 60) -> ModelBacktest:
    model = _resolve_model(model)
    if len(actuals) <= holdout_days + 30:
        return ModelBacktest(model, mae=0.0, rmse=0.0, bias=0.0, reliability_score=60.0)

    train = actuals.iloc[:-holdout_days].copy()
    holdout = actuals.iloc[-holdout_days:].copy()
    simulated = holdout[["date", "payroll", "debt_service", "capex"]].copy()
    simulated["ar_due"] = holdout["ar_due"]
    simulated["ap_due"] = holdout["ap_due"]
    simulated["currency_exposure"] = holdout["currency_exposure"]
    for column in MODEL_COLUMNS:
        simulated[column] = _forecast_component(train, holdout["date"], column, model)

    predicted_net = net_cash_flow(simulated)
    actual_net = net_cash_flow(holdout)
    errors = predicted_net - actual_net
    mae = round(float(errors.abs().mean()), 2)
    rmse = round(float(np.sqrt((errors**2).mean())), 2)
    bias = round(float(errors.mean()), 2)
    scale = max(1.0, float(actual_net.abs().mean()))
    reliability = round(max(50.0, min(94.0, 94.0 - (mae / scale) * 45.0 - abs(bias / scale) * 15.0)), 1)
    return ModelBacktest(
        model_name=model,
        mae=mae,
        rmse=rmse,
        bias=bias,
        reliability_score=reliability,
    )


def _forecast_component(
    actuals: pd.DataFrame,
    future_dates: pd.Series,
    column: str,
    model: str,
) -> np.ndarray:
    history = actuals[["date", column]].dropna().tail(365).copy()
    if history.empty:
        return np.zeros(len(future_dates))
    if model == "baseline":
        return _weekday_baseline(history, future_dates, column)
    if model == "sarimax":
        return _sarimax_forecast(history, future_dates, column)
    return _weekday_exp_smoothing(history, future_dates, column)


def _weekday_baseline(history: pd.DataFrame, future_dates: pd.Series, column: str) -> np.ndarray:
    history["weekday"] = history["date"].dt.weekday
    fallback = float(history[column].mean())
    means = history.groupby("weekday")[column].mean().to_dict()
    return np.array([max(0.0, float(means.get(day.weekday(), fallback))) for day in future_dates])


def _weekday_exp_smoothing(history: pd.DataFrame, future_dates: pd.Series, column: str, alpha: float = 0.32) -> np.ndarray:
    values = history[column].astype(float).to_numpy()
    level = float(values[0])
    for value in values[1:]:
        level = alpha * float(value) + (1 - alpha) * level

    history["weekday"] = history["date"].dt.weekday
    overall = max(0.01, float(history[column].mean()))
    weekday_factor = (history.groupby("weekday")[column].mean() / overall).to_dict()
    return np.array(
        [
            max(0.0, level * float(weekday_factor.get(day.weekday(), 1.0)))
            for day in future_dates
        ]
    )


def _sarimax_forecast(history: pd.DataFrame, future_dates: pd.Series, column: str) -> np.ndarray:
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX
    except Exception:
        return _weekday_exp_smoothing(history, future_dates, column)

    series = history.set_index("date")[column].asfreq("D").interpolate().fillna(0)
    try:
        fitted = SARIMAX(
            series,
            order=(1, 0, 1),
            seasonal_order=(1, 0, 1, 7),
            enforce_stationarity=False,
            enforce_invertibility=False,
        ).fit(disp=False)
        values = fitted.forecast(steps=len(future_dates)).to_numpy(dtype=float)
        return np.maximum(values, 0.0)
    except Exception:
        return _weekday_exp_smoothing(history, future_dates, column)


def _resolve_model(model: str) -> str:
    if model != "sarimax":
        return model
    try:
        import statsmodels  # noqa: F401
        return "sarimax"
    except Exception:
        return "exp_smoothing"


def _display_name(model: str) -> str:
    if model == "baseline":
        return "Baseline weekday means"
    if model == "sarimax":
        return "SARIMAX"
    return "Exponential smoothing"


def _model_label(model: str) -> str:
    if model == "baseline":
        return "weekday baseline"
    if model == "sarimax":
        return "SARIMAX(1,0,1)x(1,0,1,7)"
    return "weekday-adjusted exponential smoothing"
