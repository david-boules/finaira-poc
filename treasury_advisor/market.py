from __future__ import annotations

from dataclasses import dataclass

from .config import BASE_DATE


@dataclass(frozen=True)
class MarketSnapshot:
    short_term_yield: float
    borrowing_rate: float
    usd_index_change_pct: float
    fx_rate_assumption: float
    reliability_score: float
    market_event: str
    source_timestamp: str


def get_market_snapshot(scenario: str) -> MarketSnapshot:
    if scenario == "stress_receivables_fx":
        return MarketSnapshot(
            short_term_yield=5.15,
            borrowing_rate=7.35,
            usd_index_change_pct=10.0,
            fx_rate_assumption=1.10,
            reliability_score=82.0,
            market_event="Synthetic stress: USD strengthens 10% and short-term rates rise 200 bps.",
            source_timestamp=BASE_DATE.isoformat(),
        )
    if scenario == "liquidity_shortfall":
        return MarketSnapshot(
            short_term_yield=4.65,
            borrowing_rate=6.55,
            usd_index_change_pct=2.0,
            fx_rate_assumption=1.02,
            reliability_score=88.0,
            market_event="Synthetic market snapshot: borrowing costs modestly above recent baseline.",
            source_timestamp=BASE_DATE.isoformat(),
        )
    return MarketSnapshot(
        short_term_yield=4.85,
        borrowing_rate=6.25,
        usd_index_change_pct=0.5,
        fx_rate_assumption=1.00,
        reliability_score=90.0,
        market_event="Synthetic market snapshot: stable short-term yields and FX assumptions.",
        source_timestamp=BASE_DATE.isoformat(),
    )
