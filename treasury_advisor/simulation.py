from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import POLICY, TreasuryPolicy
from .forecast_models import StatisticalForecast


@dataclass(frozen=True)
class MonteCarloResult:
    percentiles: pd.DataFrame
    probability_reserve_breach: float
    probability_positive_surplus: float
    median_ending_cash: float
    p10_ending_cash: float
    p90_ending_cash: float
    stochastic_risk_score: float
    simulation_count: int
    seed: int


def run_monte_carlo(
    statistical_forecast: StatisticalForecast,
    current_cash: float,
    policy: TreasuryPolicy = POLICY,
    n_simulations: int = 1000,
    seed: int = 20260628,
) -> MonteCarloResult:
    rng = np.random.default_rng(seed)
    frame = statistical_forecast.frame.reset_index(drop=True)
    base_net = frame["net_cash_flow"].to_numpy(dtype=float)
    mae = max(1.0, statistical_forecast.backtest.mae)
    dates = frame["date"]

    paths = np.zeros((n_simulations, len(base_net)))
    for i in range(n_simulations):
        receipt_delay = rng.choice([0, 7, 15, 30], p=[0.55, 0.25, 0.15, 0.05])
        shocks = rng.normal(0, mae * 0.55, size=len(base_net))
        fx_shock = rng.normal(1.0, 0.04, size=len(base_net))
        simulated_net = base_net + shocks
        if receipt_delay:
            receipts = frame["customer_receipts"].to_numpy(dtype=float)
            delayed_receipts = pd.Series(receipts).shift(receipt_delay, fill_value=0).to_numpy()
            simulated_net += delayed_receipts - receipts
        simulated_net -= frame["fx_payments"].to_numpy(dtype=float) * (fx_shock - 1.0)
        paths[i] = current_cash + np.cumsum(simulated_net)

    p10 = np.percentile(paths, 10, axis=0)
    p50 = np.percentile(paths, 50, axis=0)
    p90 = np.percentile(paths, 90, axis=0)
    minimums = paths.min(axis=1)
    ending = paths[:, -1]
    probability_breach = round(float((minimums < policy.minimum_reserve).mean() * 100), 1)
    probability_surplus = round(float((minimums > policy.minimum_reserve + policy.liquidity_buffer).mean() * 100), 1)
    risk_score = round(max(0.0, min(100.0, 100.0 - probability_breach * 1.15)), 1)

    percentiles = pd.DataFrame(
        {
            "date": dates,
            "p10_cash": p10,
            "p50_cash": p50,
            "p90_cash": p90,
        }
    )
    return MonteCarloResult(
        percentiles=percentiles,
        probability_reserve_breach=probability_breach,
        probability_positive_surplus=probability_surplus,
        median_ending_cash=round(float(np.percentile(ending, 50)), 2),
        p10_ending_cash=round(float(np.percentile(ending, 10)), 2),
        p90_ending_cash=round(float(np.percentile(ending, 90)), 2),
        stochastic_risk_score=risk_score,
        simulation_count=n_simulations,
        seed=seed,
    )
