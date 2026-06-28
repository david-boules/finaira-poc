from __future__ import annotations

from dataclasses import dataclass

from .config import TreasuryPolicy
from .liquidity import LiquidityAnalysis
from .market import MarketSnapshot
from .quality import DataQualityResult


@dataclass(frozen=True)
class Recommendation:
    action_type: str
    title: str
    amount: float
    currency: str
    horizon_days: int
    instrument: str | None
    maturity_days: int
    required_approval: str
    requires_human_approval: bool
    ranked_options: list[dict]
    evidence: list[str]
    assumptions: list[str]
    risks: list[str]
    expected_benefit: str

    def as_dict(self) -> dict:
        return {
            "action_type": self.action_type,
            "title": self.title,
            "amount": self.amount,
            "currency": self.currency,
            "horizon_days": self.horizon_days,
            "instrument": self.instrument,
            "maturity_days": self.maturity_days,
            "required_approval": self.required_approval,
            "requires_human_approval": self.requires_human_approval,
            "ranked_options": self.ranked_options,
            "evidence": self.evidence,
            "assumptions": self.assumptions,
            "risks": self.risks,
            "expected_benefit": self.expected_benefit,
        }


def draft_recommendation(
    scenario: str,
    quality: DataQualityResult,
    analysis: LiquidityAnalysis,
    market: MarketSnapshot,
    policy: TreasuryPolicy,
) -> Recommendation:
    if quality.critical_missing:
        missing = ", ".join(quality.missing_fields) or "fresh treasury source data"
        return Recommendation(
            action_type="withhold_recommendation",
            title="Withhold recommendation until data is refreshed",
            amount=0.0,
            currency="USD",
            horizon_days=90,
            instrument=None,
            maturity_days=0,
            required_approval="None",
            requires_human_approval=False,
            ranked_options=[
                {"rank": 1, "action": "Request updated data", "reason": f"Missing or stale: {missing}"},
                {"rank": 2, "action": "Preserve cash", "reason": "No financial action without usable inputs"},
            ],
            evidence=[
                f"Completeness score: {quality.completeness_score:.1f}",
                f"Freshness score: {quality.freshness_score:.1f}; stale days: {quality.stale_days}",
            ],
            assumptions=["No numbers are inferred where source fields are missing."],
            risks=["Acting on stale or incomplete payroll, AR/AP, or cash data could violate treasury policy."],
            expected_benefit="Prevents unsupported financial advice and preserves the human approval boundary.",
        )

    if analysis.shortfall > 0:
        amount = round(analysis.shortfall + policy.liquidity_buffer, 2)
        return Recommendation(
            action_type="arrange_financing",
            title="Arrange short-term liquidity backstop",
            amount=amount,
            currency="USD",
            horizon_days=90,
            instrument=None,
            maturity_days=0,
            required_approval="CFO" if amount >= policy.cfo_approval_threshold else "Treasurer",
            requires_human_approval=True,
            ranked_options=[
                {"rank": 1, "action": "Draw or arrange revolver capacity", "reason": "Protects reserve breach"},
                {"rank": 2, "action": "Accelerate collections", "reason": "Receivables are a visible working-capital lever"},
                {"rank": 3, "action": "Defer discretionary capex", "reason": "Preserves liquidity if leadership approves"},
            ],
            evidence=[
                f"Minimum projected cash: ${analysis.minimum_projected_cash:.1f}M",
                f"Reserve shortfall: ${analysis.shortfall:.1f}M",
                f"Borrowing-rate assumption: {market.borrowing_rate:.2f}%",
            ],
            assumptions=[
                "The shortfall is measured against the configured minimum reserve.",
                "Financing is approval-gated and does not execute from this prototype.",
            ],
            risks=[
                "Borrowing costs may rise before execution.",
                "Collections actions may not recover cash inside the 90-day horizon.",
            ],
            expected_benefit="Protects minimum liquidity while treasury works receivables and timing actions.",
        )

    if scenario == "stress_receivables_fx":
        hedge_amount = round(min(analysis.protected_commitments["liquidity_buffer"] + 60.0, 110.0), 2)
        return Recommendation(
            action_type="hedge_fx",
            title="Preserve cash and hedge measured FX exposure",
            amount=hedge_amount,
            currency="USD",
            horizon_days=90,
            instrument=None,
            maturity_days=0,
            required_approval="CFO" if hedge_amount >= policy.cfo_approval_threshold else "Treasurer",
            requires_human_approval=True,
            ranked_options=[
                {"rank": 1, "action": "Preserve cash", "reason": "Receipts and FX are stressed"},
                {"rank": 2, "action": "Hedge FX exposure", "reason": "Synthetic FX shock raises dollar outflows"},
                {"rank": 3, "action": "Invest surplus", "reason": "Lower priority until stress clears"},
            ],
            evidence=[
                f"Investable surplus after protections: ${analysis.investable_surplus:.1f}M",
                f"Market event: {market.market_event}",
                f"Minimum projected cash: ${analysis.minimum_projected_cash:.1f}M",
            ],
            assumptions=[
                "FX exposure is bounded by generated 90-day obligations.",
                "Hedge recommendation is illustrative and requires human approval.",
            ],
            risks=[
                "Hedge timing and instrument choice require treasury review.",
                "Receivable delays could still reduce cash below plan.",
            ],
            expected_benefit="Reduces exposure to the stressed FX assumption while preserving liquidity.",
        )

    if analysis.investable_surplus > 25:
        amount = round(min(analysis.investable_surplus * 0.45, policy.max_counterparty_amount), 2)
        return Recommendation(
            action_type="invest_surplus",
            title="Invest bounded true surplus in a short-term instrument",
            amount=amount,
            currency="USD",
            horizon_days=60,
            instrument="Treasury bills",
            maturity_days=60,
            required_approval="CFO" if amount >= policy.cfo_approval_threshold else "Treasurer",
            requires_human_approval=True,
            ranked_options=[
                {"rank": 1, "action": "Invest true surplus", "reason": "Reserve and planned commitments remain protected"},
                {"rank": 2, "action": "Preserve cash", "reason": "Lower return but safest liquidity posture"},
                {"rank": 3, "action": "Repay debt", "reason": "Consider only if covenants and liquidity permit"},
            ],
            evidence=[
                f"Current cash: ${analysis.current_cash:.1f}M",
                f"Protected commitments total: ${sum(analysis.protected_commitments.values()):.1f}M",
                f"Calculated investable surplus: ${analysis.investable_surplus:.1f}M",
                f"Short-term yield assumption: {market.short_term_yield:.2f}%",
            ],
            assumptions=[
                "Synthetic cash-flow plan reflects known payroll, debt service, and expansion capex.",
                "Investment stays within allowed instruments, maturity, and counterparty caps.",
            ],
            risks=[
                "Unexpected customer payment delays could reduce surplus.",
                "Market yield is static mock data, not a live executable quote.",
            ],
            expected_benefit=f"Illustrative annualized yield pickup on ${amount:.1f}M while preserving policy reserves.",
        )

    return Recommendation(
        action_type="preserve_cash",
        title="Preserve cash and monitor working capital",
        amount=0.0,
        currency="USD",
        horizon_days=90,
        instrument=None,
        maturity_days=0,
        required_approval="None",
        requires_human_approval=False,
        ranked_options=[
            {"rank": 1, "action": "Preserve cash", "reason": "No genuine surplus above protected needs"},
            {"rank": 2, "action": "Improve collections", "reason": "Working capital can increase optionality"},
        ],
        evidence=[
            f"Investable surplus: ${analysis.investable_surplus:.1f}M",
            f"Minimum projected cash: ${analysis.minimum_projected_cash:.1f}M",
        ],
        assumptions=["No external execution is permitted by this prototype."],
        risks=["Liquidity headroom is limited if outflows accelerate."],
        expected_benefit="Keeps cash available until a measurable surplus or risk response emerges.",
    )
