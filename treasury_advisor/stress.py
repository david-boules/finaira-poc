from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .config import POLICY, TreasuryPolicy
from .forecast import forecast_cash
from .liquidity import analyze_liquidity


@dataclass(frozen=True)
class StressResult:
    minimum_projected_cash: float
    shortfall: float
    investable_surplus: float
    robustness_score: float
    summary: str


def run_receivables_fx_stress(
    df: pd.DataFrame, policy: TreasuryPolicy = POLICY
) -> StressResult:
    stressed = df.copy()
    future_mask = stressed["is_actual"] == False
    future = stressed[future_mask].copy()

    delayed_receipts = future["customer_receipts"].fillna(0).shift(15, fill_value=0)
    stressed.loc[future_mask, "customer_receipts"] = delayed_receipts.values
    stressed.loc[future_mask, "fx_payments"] = stressed.loc[future_mask, "fx_payments"].fillna(0) * 1.10

    forecast = forecast_cash(stressed)
    analysis = analyze_liquidity(stressed, forecast, policy)

    if analysis.shortfall > 100:
        robustness = 25.0
    elif analysis.shortfall > 0:
        robustness = 45.0
    elif analysis.investable_surplus < 50:
        robustness = 68.0
    else:
        robustness = 86.0

    if analysis.shortfall > 0:
        summary = (
            f"Stress case creates a ${analysis.shortfall:.1f}M reserve shortfall; "
            "cash preservation or financing should outrank investment."
        )
    else:
        summary = (
            f"Stress case keeps cash above reserve with ${analysis.investable_surplus:.1f}M "
            "of protected surplus remaining."
        )

    return StressResult(
        minimum_projected_cash=analysis.minimum_projected_cash,
        shortfall=analysis.shortfall,
        investable_surplus=analysis.investable_surplus,
        robustness_score=robustness,
        summary=summary,
    )
