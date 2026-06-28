from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .config import BASE_DATE


@dataclass(frozen=True)
class ForecastResult:
    frame: pd.DataFrame
    milestones: dict[int, float]
    reliability_score: float


def net_cash_flow(df: pd.DataFrame) -> pd.Series:
    return (
        df["customer_receipts"].fillna(0)
        + df["other_inflows"].fillna(0)
        - df["supplier_payments"].fillna(0)
        - df["payroll"].fillna(0)
        - df["operating_expenses"].fillna(0)
        - df["debt_service"].fillna(0)
        - df["capex"].fillna(0)
        - df["fx_payments"].fillna(0)
    )


def forecast_cash(df: pd.DataFrame) -> ForecastResult:
    actuals = df[df["date"] < BASE_DATE].copy()
    future = df[(df["date"] >= BASE_DATE) & (df["date"] < BASE_DATE + pd.Timedelta(days=90))].copy()
    start_cash = float(actuals.iloc[-1]["closing_cash"])

    future["net_cash_flow"] = net_cash_flow(future)
    future["day_number"] = range(1, len(future) + 1)
    future["projected_cash"] = start_cash + future["net_cash_flow"].cumsum()

    historical_net = net_cash_flow(actuals.tail(180))
    volatility = float(historical_net.std()) if len(historical_net) > 1 else 0.0
    future["lower_bound"] = future["projected_cash"] - 0.35 * volatility * (future["day_number"] ** 0.5)
    future["upper_bound"] = future["projected_cash"] + 0.35 * volatility * (future["day_number"] ** 0.5)

    milestones = {}
    for horizon in (30, 60, 90):
        idx = min(horizon - 1, len(future) - 1)
        milestones[horizon] = round(float(future.iloc[idx]["projected_cash"]), 2)

    average_cash = max(1.0, abs(start_cash))
    volatility_ratio = volatility / average_cash
    reliability = round(max(55.0, min(92.0, 92.0 - volatility_ratio * 180.0)), 1)

    return ForecastResult(
        frame=future[
            [
                "date",
                "net_cash_flow",
                "projected_cash",
                "lower_bound",
                "upper_bound",
                "customer_receipts",
                "supplier_payments",
                "payroll",
                "debt_service",
                "capex",
                "fx_payments",
                "ar_due",
                "ap_due",
                "currency_exposure",
            ]
        ].copy(),
        milestones=milestones,
        reliability_score=reliability,
    )
