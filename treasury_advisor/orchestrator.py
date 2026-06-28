from __future__ import annotations

from dataclasses import asdict
from uuid import uuid4

from .audit import append_audit_record
from .config import POLICY
from .decision import draft_recommendation
from .forecast import forecast_cash
from .liquidity import analyze_liquidity
from .market import get_market_snapshot
from .policy import evaluate_policy
from .quality import validate_data
from .stress import run_receivables_fx_stress
from .synthetic_data import ensure_synthetic_data, load_scenario_data
from .confidence import evaluate_confidence
from .forecast_models import fit_statistical_forecast
from .llm_adapter import generate_explanation
from .rag import retrieve_policy_context
from .simulation import run_monte_carlo
from .agent_trace import build_agent_trace
from .guardrails import validate_grounding


def run_scenario(
    scenario: str,
    log_recommendation: bool = False,
    forecast_model: str = "exp_smoothing",
    simulation_seed: int = 20260628,
    llm_provider: str = "ollama",
    llm_model: str | None = None,
) -> dict:
    ensure_synthetic_data()
    df = load_scenario_data(scenario)
    quality = validate_data(df)
    forecast = forecast_cash(df)
    analysis = analyze_liquidity(df, forecast, POLICY)
    statistical_forecast = fit_statistical_forecast(df, model=forecast_model)
    simulation = run_monte_carlo(
        statistical_forecast=statistical_forecast,
        current_cash=analysis.current_cash,
        policy=POLICY,
        seed=simulation_seed,
    )
    market = get_market_snapshot(scenario)
    stress = run_receivables_fx_stress(df, POLICY)
    recommendation = draft_recommendation(scenario, quality, analysis, market, POLICY)
    policy = evaluate_policy(recommendation.as_dict(), analysis.investable_surplus, POLICY)
    confidence = evaluate_confidence(
        quality=quality,
        policy=policy,
        forecast_reliability=forecast.reliability_score,
        market_reliability=market.reliability_score,
        stress_robustness=stress.robustness_score,
        traceable=True,
        stochastic_risk_score=simulation.stochastic_risk_score,
        probability_reserve_breach=simulation.probability_reserve_breach,
    )
    policy_context = retrieve_policy_context(
        " ".join([recommendation.title, recommendation.action_type, *recommendation.evidence])
    )
    explanation = generate_explanation(
        {
            "recommendation": recommendation,
            "confidence": confidence,
            "analysis": analysis,
            "simulation": simulation,
        },
        policy_context,
        provider_preference=llm_provider,
        model_name=llm_model,
    )

    run_id = str(uuid4())
    result = {
        "run_id": run_id,
        "scenario": scenario,
        "data": df,
        "quality": quality,
        "forecast": forecast,
        "analysis": analysis,
        "statistical_forecast": statistical_forecast,
        "simulation": simulation,
        "market": market,
        "stress": stress,
        "recommendation": recommendation,
        "policy": policy,
        "confidence": confidence,
        "policy_context": policy_context,
        "explanation": explanation,
    }
    result["grounding"] = validate_grounding(result)
    result["agent_trace"] = build_agent_trace(result)
    if log_recommendation:
        append_audit_record(make_audit_record(result, "recommendation"))
    return result


def make_audit_record(result: dict, event_type: str, human_decision: str | None = None, outcome: str | None = None) -> dict:
    return {
        "event_type": event_type,
        "run_id": result["run_id"],
        "scenario": result["scenario"],
        "data_timestamps": {
            "latest_internal_data": result["data"]["data_updated_at"].max().isoformat(),
            "market_snapshot": result["market"].source_timestamp,
        },
        "tool_outputs": {
            "quality": asdict(result["quality"]),
            "analysis": asdict(result["analysis"]),
            "stress": asdict(result["stress"]),
            "statistical_forecast": {
                "model_name": result["statistical_forecast"].model_name,
                "backtest": asdict(result["statistical_forecast"].backtest),
            },
            "monte_carlo": {
                "probability_reserve_breach": result["simulation"].probability_reserve_breach,
                "probability_positive_surplus": result["simulation"].probability_positive_surplus,
                "median_ending_cash": result["simulation"].median_ending_cash,
                "p10_ending_cash": result["simulation"].p10_ending_cash,
                "p90_ending_cash": result["simulation"].p90_ending_cash,
                "simulation_count": result["simulation"].simulation_count,
            },
        },
        "recommendation": result["recommendation"].as_dict(),
        "policy_results": {
            "passed": result["policy"].passed,
            "required_approval": result["policy"].required_approval,
            "checks": [asdict(check) for check in result["policy"].checks],
        },
        "confidence": asdict(result["confidence"]),
        "llm_explanation": result["explanation"],
        "human_decision": human_decision,
        "outcome": outcome,
        "assumptions": result["recommendation"].assumptions,
    }
