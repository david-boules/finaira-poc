from __future__ import annotations


def build_agent_trace(result: dict) -> list[dict]:
    quality = result["quality"]
    analysis = result["analysis"]
    statistical_forecast = result["statistical_forecast"]
    simulation = result["simulation"]
    stress = result["stress"]
    recommendation = result["recommendation"]
    policy = result["policy"]
    confidence = result["confidence"]
    explanation = result["explanation"]
    grounding = result["grounding"]

    return [
        {
            "id": "request",
            "agent": "Scope Guardrail",
            "role": "Allows only corporate treasury requests; redirects unrelated or personal-investment requests before the supervisor runs.",
            "status": "complete",
            "output": f"Scenario routed: {result['scenario'].replace('_', ' ')}.",
            "handoff": "Passes scoped request to data ingestion.",
        },
        {
            "id": "data",
            "agent": "Data Quality Guardrail",
            "role": "Blocks recommendations based on stale, missing, conflicting, or unreliable information.",
            "status": "attention" if quality.critical_missing else "complete",
            "output": (
                f"Completeness {quality.completeness_score:.1f}%, freshness {quality.freshness_score:.1f}%, "
                f"stale days {quality.stale_days}."
            ),
            "handoff": "Provides validated source data to forecasting.",
        },
        {
            "id": "cashflow",
            "agent": "Cashflow Forecast Agent",
            "role": "Runs deterministic 30/60/90-day forecast plus statistical component forecast.",
            "status": "complete",
            "output": (
                f"90-day cash {analysis.horizon_values[90]:.1f}M; model {statistical_forecast.model_name}; "
                f"backtest MAE {statistical_forecast.backtest.mae:.1f}M."
            ),
            "handoff": "Sends forecast path and model reliability to liquidity analysis.",
        },
        {
            "id": "grounding",
            "agent": "Grounding Guardrail",
            "role": "Prevents hallucinated balances, rates, returns, and recommendation amounts.",
            "status": "complete" if grounding.passed else "blocked",
            "output": grounding.message,
            "handoff": "Only grounded numbers are allowed into recommendation and narrative layers.",
        },
        {
            "id": "insight",
            "agent": "Insight Agent",
            "role": "Detects surplus, shortfall, and working-capital weak points.",
            "status": "attention" if analysis.shortfall > 0 else "complete",
            "output": (
                f"Investable surplus {analysis.investable_surplus:.1f}M; reserve shortfall "
                f"{analysis.shortfall:.1f}M."
            ),
            "handoff": "Frames the financial problem for risk and capital allocation agents.",
        },
        {
            "id": "risk",
            "agent": "Risk Agent",
            "role": "Runs Monte Carlo reserve-breach probability and receivables/FX stress testing.",
            "status": "attention" if simulation.probability_reserve_breach > 15 or stress.shortfall > 0 else "complete",
            "output": (
                f"Reserve-breach probability {simulation.probability_reserve_breach:.1f}%; "
                f"stress shortfall {stress.shortfall:.1f}M."
            ),
            "handoff": "Passes stochastic risk evidence to the confidence gate.",
        },
        {
            "id": "capital",
            "agent": "Capital Allocation Agent",
            "role": "Compares preserve cash, invest surplus, financing, working-capital, debt, and FX actions.",
            "status": "complete",
            "output": f"Draft action: {recommendation.title}; amount {recommendation.amount:.1f}M.",
            "handoff": "Sends draft action to policy enforcement.",
        },
        {
            "id": "policy",
            "agent": "Treasury Policy Engine",
            "role": "Machine-readable rules for reserves, permitted assets, maturity, counterparty exposure, and approval authority.",
            "status": "complete" if policy.passed else "blocked",
            "output": f"{sum(1 for check in policy.checks if check.passed)}/{len(policy.checks)} checks passed.",
            "handoff": "Blocks, warns, or clears the draft for confidence scoring.",
        },
        {
            "id": "confidence",
            "agent": "Decision Confidence Gate",
            "role": "Uses evidence quality, forecast reliability, policy compliance, and stress performance; never LLM self-confidence.",
            "status": "blocked" if confidence.status in {"BLOCK", "WITHHOLD"} else ("attention" if confidence.status in {"REQUEST DATA", "RECOMMEND WITH WARNING"} else "complete"),
            "output": f"{confidence.status} at {confidence.score:.1f}/100.",
            "handoff": "Determines whether to show, warn, request more data, withhold, or block.",
        },
        {
            "id": "reporting",
            "agent": "Reporting Agent",
            "role": "Retrieves policy context and produces the treasurer-ready explanation.",
            "status": "complete",
            "output": f"Narrative provider: {explanation['provider']}.",
            "handoff": "Presents recommendation and evidence to the human approver.",
        },
        {
            "id": "approval",
            "agent": "Human-in-the-Loop Checkpoint",
            "role": "Requires approval before investment, financing, transfer, FX, debt, or payment-delay execution.",
            "status": "attention" if recommendation.requires_human_approval else "complete",
            "output": f"Required approval: {policy.required_approval}. No execution occurs in the prototype.",
            "handoff": "Logs human decision and outcome to audit memory.",
        },
    ]
