from dataclasses import dataclass
from pathlib import Path

import pandas as pd


BASE_DATE = pd.Timestamp("2026-06-27")
DATA_DIR = Path("data")
AUDIT_LOG_PATH = DATA_DIR / "audit_log.jsonl"
USD_M = "USD millions"


SCENARIOS = {
    "healthy_surplus": "Scenario 1",
    "liquidity_shortfall": "Scenario 2",
    "stale_missing_data": "Scenario 3",
    "stress_receivables_fx": "Scenario 4",
}


@dataclass(frozen=True)
class TreasuryPolicy:
    minimum_reserve: float = 300.0
    liquidity_buffer: float = 50.0
    max_investment_maturity_days: int = 90
    max_counterparty_amount: float = 200.0
    allowed_instruments: tuple[str, ...] = (
        "Treasury bills",
        "Government money market fund",
        "Insured bank deposit",
    )
    cfo_approval_threshold: float = 100.0
    high_impact_actions: tuple[str, ...] = (
        "invest_surplus",
        "arrange_financing",
        "hedge_fx",
        "repay_debt",
        "transfer_cash",
        "delay_payment",
    )


POLICY = TreasuryPolicy()
