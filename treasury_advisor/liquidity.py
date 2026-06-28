from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .config import BASE_DATE, TreasuryPolicy
from .forecast import ForecastResult


@dataclass(frozen=True)
class LiquidityAnalysis:
    current_cash: float
    minimum_projected_cash: float
    shortfall: float
    investable_surplus: float
    protected_commitments: dict[str, float]
    weak_points: list[str]
    horizon_values: dict[int, float]


def analyze_liquidity(
    df: pd.DataFrame, forecast: ForecastResult, policy: TreasuryPolicy
) -> LiquidityAnalysis:
    actuals = df[df["date"] < BASE_DATE]
    future = df[(df["date"] >= BASE_DATE) & (df["date"] < BASE_DATE + pd.Timedelta(days=90))]
    current_cash = round(float(actuals.iloc[-1]["closing_cash"]), 2)
    minimum_projected_cash = round(float(forecast.frame["projected_cash"].min()), 2)
    shortfall = round(max(0.0, policy.minimum_reserve - minimum_projected_cash), 2)

    protected_commitments = {
        "minimum_reserve": policy.minimum_reserve,
        "payroll_30d": round(float(future.head(30)["payroll"].fillna(0).sum()), 2),
        "debt_service_90d": round(float(future["debt_service"].fillna(0).sum()), 2),
        "planned_expansion_capex_90d": round(float(future["capex"].fillna(0).sum()), 2),
        "liquidity_buffer": policy.liquidity_buffer,
    }
    protected_total = sum(protected_commitments.values())
    investable_surplus = round(max(0.0, current_cash - protected_total), 2)
    if shortfall > 0:
        investable_surplus = 0.0

    weak_points = []
    if shortfall > 0:
        weak_points.append(
            f"Projected cash falls ${shortfall:.1f}M below the minimum reserve."
        )
    if future["ar_due"].fillna(0).sum() > future["customer_receipts"].fillna(0).sum() * 1.28:
        weak_points.append("Receivables due are elevated versus expected cash receipts.")
    if future["ap_due"].fillna(0).max() > future["ap_due"].fillna(0).median() * 2.2:
        weak_points.append("Payables show a concentration that may create timing pressure.")
    if future["currency_exposure"].fillna(0).sum() > 190:
        weak_points.append("FX-denominated obligations are material within the 90-day horizon.")
    if not weak_points:
        weak_points.append("No material liquidity or working-capital weakness detected.")

    return LiquidityAnalysis(
        current_cash=current_cash,
        minimum_projected_cash=minimum_projected_cash,
        shortfall=shortfall,
        investable_surplus=investable_surplus,
        protected_commitments=protected_commitments,
        weak_points=weak_points,
        horizon_values=forecast.milestones,
    )
