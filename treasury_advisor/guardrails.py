from __future__ import annotations

from dataclasses import dataclass


TREASURY_TERMS = {
    "treasury",
    "cash",
    "liquidity",
    "working capital",
    "receivable",
    "receivables",
    "payable",
    "payables",
    "payroll",
    "debt",
    "capex",
    "reserve",
    "financing",
    "fx",
    "hedge",
    "investment policy",
    "corporate",
    "shortfall",
    "surplus",
}

OUT_OF_SCOPE_TERMS = {
    "personal portfolio",
    "my portfolio",
    "my retirement",
    "401k",
    "roth ira",
    "personal investment",
    "buy stocks",
    "which stock",
    "crypto",
    "bitcoin",
    "mortgage",
    "student loan",
    "sports",
    "recipe",
    "travel",
}


@dataclass(frozen=True)
class ScopeResult:
    in_scope: bool
    label: str
    reason: str
    redirect_message: str


@dataclass(frozen=True)
class GroundingResult:
    passed: bool
    sources: list[dict]
    message: str


def classify_treasury_scope(user_request: str) -> ScopeResult:
    normalized = user_request.lower().strip()
    if not normalized:
        return ScopeResult(
            in_scope=True,
            label="corporate_treasury",
            reason="Default demo request is a corporate treasury scenario.",
            redirect_message="",
        )

    out_hits = [term for term in OUT_OF_SCOPE_TERMS if term in normalized]
    in_hits = [term for term in TREASURY_TERMS if term in normalized]
    if out_hits and not in_hits:
        return ScopeResult(
            in_scope=False,
            label="out_of_scope",
            reason=f"Detected non-corporate-treasury request terms: {', '.join(out_hits)}.",
            redirect_message=(
                "I can only assist with corporate treasury topics such as liquidity, cash forecasting, "
                "working capital, debt service, FX exposure, policy checks, and approval-gated treasury actions."
            ),
        )

    return ScopeResult(
        in_scope=True,
        label="corporate_treasury",
        reason="Request contains corporate treasury context or matches the demo treasury workflow.",
        redirect_message="",
    )


def validate_grounding(result: dict) -> GroundingResult:
    recommendation = result["recommendation"]
    sources = [
        {
            "claim": "current cash",
            "value": result["analysis"].current_cash,
            "source": "synthetic treasury CSV + deterministic liquidity analysis",
        },
        {
            "claim": "30/60/90-day projected cash",
            "value": result["analysis"].horizon_values,
            "source": "deterministic cash-flow forecast",
        },
        {
            "claim": "investable surplus",
            "value": result["analysis"].investable_surplus,
            "source": "protected-commitment surplus calculator",
        },
        {
            "claim": "reserve-breach probability",
            "value": result["simulation"].probability_reserve_breach,
            "source": "Monte Carlo simulation",
        },
        {
            "claim": "recommended amount",
            "value": recommendation.amount,
            "source": "capital-allocation decision engine",
        },
        {
            "claim": "market rates",
            "value": {
                "short_term_yield": result["market"].short_term_yield,
                "borrowing_rate": result["market"].borrowing_rate,
            },
            "source": "synthetic market-intelligence adapter",
        },
    ]
    missing = [
        item["claim"]
        for item in sources
        if item["value"] is None or item["value"] == ""
    ]
    return GroundingResult(
        passed=not missing,
        sources=sources,
        message=(
            "Every displayed financial number is tied to source data or deterministic tool output."
            if not missing
            else f"Missing grounding for: {', '.join(missing)}."
        ),
    )
