from __future__ import annotations

from dataclasses import dataclass

from .policy import PolicyResult
from .quality import DataQualityResult


@dataclass(frozen=True)
class ConfidenceDecision:
    score: float
    status: str
    factors: dict[str, float]
    message: str


def evaluate_confidence(
    quality: DataQualityResult,
    policy: PolicyResult,
    forecast_reliability: float,
    market_reliability: float,
    stress_robustness: float,
    traceable: bool,
    stochastic_risk_score: float | None = None,
    probability_reserve_breach: float | None = None,
) -> ConfidenceDecision:
    if not policy.passed:
        return ConfidenceDecision(
            score=0.0,
            status="BLOCK",
            factors={},
            message="A hard treasury policy failed; recommendation is blocked and should be escalated.",
        )

    factors = {
        "data_completeness": quality.completeness_score,
        "data_freshness": quality.freshness_score,
        "forecast_reliability": forecast_reliability,
        "market_reliability": market_reliability,
        "stress_robustness": stress_robustness,
        "traceability": 100.0 if traceable else 0.0,
    }
    if stochastic_risk_score is not None:
        factors["stochastic_risk"] = stochastic_risk_score
    if probability_reserve_breach is not None:
        factors["reserve_breach_probability"] = round(100.0 - probability_reserve_breach, 1)

    stochastic_component = stochastic_risk_score if stochastic_risk_score is not None else stress_robustness
    score = round(
        factors["data_completeness"] * 0.25
        + factors["data_freshness"] * 0.20
        + factors["forecast_reliability"] * 0.17
        + factors["market_reliability"] * 0.10
        + factors["stress_robustness"] * 0.10
        + stochastic_component * 0.08
        + factors["traceability"] * 0.10,
        1,
    )

    if quality.critical_missing:
        return ConfidenceDecision(
            score=score,
            status="REQUEST DATA",
            factors=factors,
            message="Critical data is missing or stale; request updated inputs before recommending action.",
        )
    if score >= 80:
        status = "RECOMMEND"
        message = "Evidence is sufficient to show the recommendation with standard approval controls."
    elif score >= 60:
        status = "RECOMMEND WITH WARNING"
        message = "Evidence supports the recommendation, but the user should review warnings."
    else:
        status = "REQUEST DATA"
        message = "Evidence is too weak to recommend action; request more data."

    return ConfidenceDecision(score=score, status=status, factors=factors, message=message)
