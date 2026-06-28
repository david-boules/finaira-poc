import pandas as pd
import streamlit as st
from html import escape

from treasury_advisor.audit import append_audit_record, audit_dataframe
from treasury_advisor.config import BASE_DATE, POLICY, SCENARIOS, USD_M
from treasury_advisor.guardrails import classify_treasury_scope
from treasury_advisor.orchestrator import make_audit_record, run_scenario


st.set_page_config(
    page_title="HiveFin: An Agentic Corporate Treasury Advisor",
    page_icon="",
    layout="wide",
)


def money(value: float) -> str:
    return f"${value:,.1f}M"


def md_safe(text: str) -> str:
    """Escape dollar signs so Streamlit markdown does not treat amounts as LaTeX."""
    return text.replace("$", r"\$")


def info_box(text: str) -> None:
    st.markdown(
        f'<div class="hive-info-box">{escape(text)}</div>',
        unsafe_allow_html=True,
    )


def status_badge(status: str) -> str:
    colors = {
        "RECOMMEND": "#0f766e",
        "RECOMMEND WITH WARNING": "#a16207",
        "REQUEST DATA": "#b45309",
        "WITHHOLD": "#991b1b",
        "BLOCK": "#7f1d1d",
    }
    return (
        f'<div class="status-badge-wrap">'
        f"<span style='background:{colors.get(status, '#334155')}; color:white; "
        "padding:0.25rem 0.55rem; border-radius:999px; font-weight:700;'>"
        f"{status}</span></div>"
    )


def data_quality_evidence(quality) -> str:
    details = [
        f"Completeness {quality.completeness_score:.1f}%",
        f"freshness {quality.freshness_score:.1f}%",
        f"stale days {quality.stale_days}",
    ]
    if quality.missing_fields:
        details.append(f"missing fields: {', '.join(quality.missing_fields)}")
    if quality.consistency_issues:
        details.append(f"issues: {'; '.join(quality.consistency_issues)}")
    return ". ".join(details) + "."


def render_data_quality_panel(quality) -> None:
    st.write("Data quality output")
    rows = [
        {"check": "Completeness score", "result": f"{quality.completeness_score:.1f}%"},
        {"check": "Freshness score", "result": f"{quality.freshness_score:.1f}%"},
        {"check": "Stale days", "result": str(quality.stale_days)},
        {
            "check": "Missing fields",
            "result": ", ".join(quality.missing_fields) if quality.missing_fields else "None",
        },
        {
            "check": "Consistency issues",
            "result": "; ".join(quality.consistency_issues) if quality.consistency_issues else "None",
        },
        {"check": "Usable for recommendation", "result": "Yes" if quality.usable else "No"},
    ]
    st.dataframe(pd.DataFrame(rows), hide_index=True)
    if quality.missing_fields or quality.consistency_issues or not quality.usable:
        missing = ", ".join(quality.missing_fields) if quality.missing_fields else "fresh treasury source data"
        st.warning(
            md_safe(
                "Request data before action: refresh the treasury dataset and provide "
                f"{missing}. No recommendation should proceed until the quality gate passes."
            )
        )


def record_once(result: dict) -> None:
    key = f"logged_{result['scenario']}_{result['run_id']}"
    if not st.session_state.get(key):
        append_audit_record(make_audit_record(result, "recommendation"))
        st.session_state[key] = True


st.markdown(
    """
    <style>
    :root {
        --finaira-ink:#071923;
        --finaira-navy:#0b2633;
        --finaira-teal:#00a99d;
        --finaira-cyan:#21d4c2;
        --finaira-mint:#e9fbf7;
        --finaira-surface:#ffffff;
        --finaira-soft:#f5f8fa;
        --finaira-line:#dce8ea;
        --finaira-slate:#55707a;
        --finaira-amber:#b7791f;
        --finaira-red:#b42318;
    }
    html, body, [data-testid="stAppViewContainer"] {
        background: var(--finaira-soft);
        color: var(--finaira-ink);
    }
    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid var(--finaira-line);
    }
    .block-container {
        padding-top: 1.4rem;
        max-width: 1480px;
    }
    [data-testid="stMarkdownContainer"] {
        overflow: visible;
    }
    [data-testid="stMarkdownContainer"] > div {
        overflow: visible;
        max-width: 100%;
    }
    .finaira-header {
        background: linear-gradient(135deg, #071923 0%, #0b3640 62%, #0f766e 100%);
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.12);
        padding: 1.15rem 1.25rem;
        margin-bottom: 1rem;
        color: white;
        box-shadow: 0 16px 40px rgba(7,25,35,0.16);
        width: 100%;
        max-width: 100%;
        box-sizing: border-box;
        text-align: center;
        overflow: visible;
    }
    .finaira-header-title {
        margin: 0;
        font-size: clamp(1.2rem, 2.2vw, 1.85rem);
        font-weight: 700;
        line-height: 1.35;
        letter-spacing: 0;
        text-align: center;
        color: #ffffff;
        white-space: normal;
        overflow: visible;
        overflow-wrap: anywhere;
        word-break: normal;
    }
    .synthetic-banner {
        background:#fff8e6;
        border:1px solid #f3d28b;
        color:#6f4c00;
        padding:0.75rem 1rem;
        border-radius:6px;
        font-weight:700;
        margin-bottom:1rem;
        width: 100%;
        max-width: 100%;
        box-sizing: border-box;
        text-align: center;
        line-height: 1.4;
        overflow: visible;
        overflow-wrap: anywhere;
    }
    .status-badge-wrap {
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .hive-info-box {
        background: #e8f4fd;
        border: 1px solid #b9daf7;
        border-radius: 0.5rem;
        padding: 1rem 1.1rem;
        color: #1e3a5f;
        font-size: 1rem;
        line-height: 1.55;
        margin: 0.25rem 0 1rem 0;
    }
    .small-muted { color:#64748b; font-size:0.9rem; }
    .workflow-container {
        display:flex;
        overflow-x:auto;
        gap:0.45rem;
        padding:0.5rem;
        background:white;
        border:1px solid var(--finaira-line);
        border-radius:8px;
        margin-bottom:1rem;
        width: 100%;
        max-width: 100%;
        box-sizing: border-box;
    }
    .workflow-step {
        flex:1;
        min-width:110px;
        padding:0.55rem 0.45rem;
        border-radius:6px;
        font-size:0.76rem;
        font-weight:700;
        text-align:center;
        border:1px solid var(--finaira-line);
        color:var(--finaira-slate);
        background:#f8fbfb;
        display:flex;
        align-items:center;
        justify-content:center;
        line-height:1.25;
        overflow-wrap:anywhere;
    }
    .workflow-step.complete { color:#075e54; background:#e7fbf5; border-color:#a8ece0; }
    .workflow-step.attention { color:#855a00; background:#fff7df; border-color:#f2d38b; }
    .workflow-step.blocked { color:#8b1d16; background:#fff0ee; border-color:#f2b8b3; }
    .small-muted { color:#64748b; font-size:0.9rem; }
    .architecture-band {
        background:white;
        border:1px solid var(--finaira-line);
        border-radius:8px;
        padding:1rem;
        margin-bottom:1rem;
        width: 100%;
        max-width: 100%;
        box-sizing: border-box;
        text-align: center;
    }
    .arch-grid {
        display:grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap:0.7rem;
    }
    .arch-node {
        border:1px solid var(--finaira-line);
        border-radius:8px;
        padding:0.8rem;
        background:#fbfefe;
        min-height:110px;
        text-align: center;
        display:flex;
        flex-direction:column;
        align-items:center;
        justify-content:center;
    }
    .arch-node strong {
        color:var(--finaira-navy);
        display:block;
        text-align:center;
    }
    .arch-node span {
        display:block;
        color:var(--finaira-slate);
        font-size:0.82rem;
        margin-top:0.35rem;
        text-align:center;
        line-height:1.35;
    }
    @media (max-width: 900px) {
        .arch-grid { grid-template-columns: 1fr; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    "<div class='synthetic-banner'>Synthetic / illustrative data only. This is not actual company financial data and does not execute financial transactions.</div>",
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="finaira-header"><div class="finaira-header-title">HiveFin: An Agentic Corporate Treasury Advisor</div></div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Run Controls")
    user_request = st.text_area(
        "Treasury request",
        value="Assess corporate liquidity, investable surplus, FX exposure, and approval requirements.",
        height=80,
    )
    scenario = st.selectbox(
        "Scenario",
        options=list(SCENARIOS.keys()),
        format_func=lambda value: SCENARIOS[value],
    )
    forecast_model = st.selectbox(
        "Forecast model",
        options=["exp_smoothing", "baseline", "sarimax"],
        format_func=lambda value: {
            "exp_smoothing": "Exponential smoothing",
            "baseline": "Weekday baseline",
            "sarimax": "SARIMAX if statsmodels is installed",
        }[value],
    )
    simulation_seed = st.number_input("Monte Carlo seed", value=20260628, step=1)
    llm_provider = st.selectbox(
        "Explanation provider",
        options=["ollama", "template"],
        index=0,
        format_func=lambda value: {
            "ollama": "Local Ollama",
            "template": "Template fallback",
        }[value],
    )
    llm_model = st.text_input("Explanation model", value="llama3.2")
    scope = classify_treasury_scope(user_request)
    st.write("Scope gate:", "PASS" if scope.in_scope else "REDIRECT")
    st.write("Reference date:", BASE_DATE.date().isoformat())
    st.write("Role/access placeholder: Corporate Treasurer")
    st.divider()
    st.write("Policy")
    st.write(f"Minimum reserve: {money(POLICY.minimum_reserve)}")
    st.write(f"Max maturity: {POLICY.max_investment_maturity_days} days")
    st.write(f"Counterparty cap: {money(POLICY.max_counterparty_amount)}")

scope_result = classify_treasury_scope(user_request)
if not scope_result.in_scope:
    st.error("Scope Guardrail: request redirected")
    st.write(scope_result.reason)
    st.info(scope_result.redirect_message)
    st.stop()

result = run_scenario(
    scenario,
    forecast_model=forecast_model,
    simulation_seed=int(simulation_seed),
    llm_provider=llm_provider,
    llm_model=llm_model.strip() or None,
)
record_once(result)

quality = result["quality"]
forecast = result["forecast"]
analysis = result["analysis"]
statistical_forecast = result["statistical_forecast"]
simulation = result["simulation"]
market = result["market"]
stress = result["stress"]
recommendation = result["recommendation"]
policy = result["policy"]
confidence = result["confidence"]
explanation = result["explanation"]
agent_trace = result["agent_trace"]
grounding = result["grounding"]

def render_workflow_stepper(trace: list[dict]) -> None:
    parts = []
    for step in trace:
        label = escape(step["agent"])
        status = escape(step["status"])
        parts.append(f'<span class="workflow-step {status}">{label}</span>')
    st.markdown(
        '<div class="workflow-container">' + "".join(parts) + "</div>",
        unsafe_allow_html=True,
    )


def render_agent_cards(trace: list[dict]) -> None:
    for step in trace:
        status = step["status"]
        label = f"{step['agent']} — {status.upper()}"
        with st.expander(label, expanded=False):
            st.caption(step["role"])
            st.write(step["output"])
            st.caption(f"Handoff: {step['handoff']}")


def render_architecture() -> None:
    nodes = [
        ("Corporate Request", "Scenario, role, scope, and user intent."),
        ("Internal + External Data", "Synthetic treasury ledger, market snapshot, policy docs."),
        ("Processing Pipeline", "Request, ingestion, cashflow, insight, risk, investment, reporting."),
        ("Deterministic Tools", "Forecasts, surplus math, Monte Carlo, stress, policy checks."),
        ("Knowledge + RAG", "Synthetic treasury, investment, and liquidity policy retrieval."),
        ("LLM Narrative", "Ollama or template explanation using structured tool outputs."),
        ("Confidence Gate", "Recommend, warn, request data, withhold, or block."),
        ("Human Approval", "Approve, modify, reject, and write audit memory."),
    ]
    html = "".join(
        f'<div class="arch-node"><strong>{escape(title)}</strong><span>{escape(body)}</span></div>'
        for title, body in nodes
    )
    st.markdown('<div class="architecture-band"><div class="arch-grid">' + html + "</div></div>", unsafe_allow_html=True)


workflow_tab, walkthrough_tab, dashboard_tab, analysis_tab, recommendation_tab, approval_tab, audit_tab = st.tabs(
    ["Workflow", "Architecture", "Dashboard", "Analysis", "Recommendation", "Approval", "Audit"]
)

with workflow_tab:
    st.subheader("Live Execution Trace")
    st.caption("Request, data ingestion, cashflow forecast, insight, risk, investment, reporting, and human approval.")
    render_workflow_stepper(agent_trace)
    render_agent_cards(agent_trace)
    st.subheader("Guardrail Status")
    guardrail_rows = [
        {"guardrail": "Scope", "status": "PASS", "evidence": scope_result.reason},
        {"guardrail": "Data Quality", "status": "PASS" if quality.usable else "ATTENTION", "evidence": data_quality_evidence(quality)},
        {"guardrail": "Grounding", "status": "PASS" if grounding.passed else "BLOCK", "evidence": grounding.message},
        {"guardrail": "Treasury Policy", "status": "PASS" if policy.passed else "BLOCK", "evidence": f"{sum(1 for check in policy.checks if check.passed)}/{len(policy.checks)} checks passed."},
        {"guardrail": "Decision Confidence", "status": confidence.status, "evidence": confidence.message},
        {"guardrail": "Human-in-the-Loop", "status": "REQUIRED" if recommendation.requires_human_approval else "NOT REQUIRED", "evidence": f"Approval authority: {policy.required_approval}."},
    ]
    st.dataframe(pd.DataFrame(guardrail_rows), hide_index=True)
    render_data_quality_panel(quality)

with walkthrough_tab:
    st.subheader("Architecture Overview")
    render_architecture()
    st.write("1. User request is scoped to corporate treasury.")
    st.write("2. Data ingestion loads internal treasury data and external/static market context.")
    st.write("3. The cashflow forecast agent projects cash; insight and risk modules diagnose surplus or shortfall.")
    st.write("4. The investment agent compares actions under stress and stochastic simulation.")
    st.write("5. Reporting retrieves policy context and writes the narrative.")
    st.write("6. Confidence gate and human approval checkpoint control what can be shown or logged.")
    st.info(
        "Model stack: deterministic roll-forward, optional statistical model, 1,000-path Monte Carlo, static market adapter, "
        "keyword RAG over synthetic policy docs, optional Ollama narrative, deterministic policy gate."
    )
    st.write("Current LLM provider:", explanation["provider"])

with dashboard_tab:
    st.subheader(SCENARIOS[scenario])
    st.markdown(status_badge(confidence.status), unsafe_allow_html=True)
    st.write(confidence.message)

    cols = st.columns(6)
    cols[0].metric("Current Cash", money(analysis.current_cash))
    cols[1].metric("30-Day Cash", money(analysis.horizon_values[30]))
    cols[2].metric("60-Day Cash", money(analysis.horizon_values[60]))
    cols[3].metric("90-Day Cash", money(analysis.horizon_values[90]))
    cols[4].metric("Genuine Surplus", money(analysis.investable_surplus))
    cols[5].metric("Confidence", f"{confidence.score:.1f}")

    risk_cols = st.columns(4)
    risk_cols[0].metric("Model", statistical_forecast.model_name)
    risk_cols[1].metric("Backtest MAE", money(statistical_forecast.backtest.mae))
    risk_cols[2].metric("Reserve Breach Prob.", f"{simulation.probability_reserve_breach:.1f}%")
    risk_cols[3].metric("MC Ending Cash P10/P50", f"{money(simulation.p10_ending_cash)} / {money(simulation.median_ending_cash)}")

    alert = (
        f"Projected reserve shortfall: {money(analysis.shortfall)}"
        if analysis.shortfall > 0
        else f"Recommended action: {recommendation.title}"
    )
    if confidence.status in {"BLOCK", "REQUEST DATA", "WITHHOLD"}:
        st.warning(md_safe(alert))
        render_data_quality_panel(quality)
    elif confidence.status == "RECOMMEND WITH WARNING":
        st.warning(md_safe(alert))
    else:
        st.success(md_safe(alert))

    chart = forecast.frame[["date", "projected_cash", "lower_bound", "upper_bound"]].set_index("date")
    st.line_chart(chart)

with analysis_tab:
    st.subheader("Cash Forecast and Working Capital")
    left, right = st.columns([2, 1])
    with left:
        flow_chart = forecast.frame[
            [
                "date",
                "customer_receipts",
                "supplier_payments",
                "payroll",
                "debt_service",
                "capex",
                "fx_payments",
            ]
        ].set_index("date")
        st.bar_chart(flow_chart)
    with right:
        st.write("Protected commitments")
        st.dataframe(
            pd.DataFrame(
                [
                    {"item": key.replace("_", " "), "amount": value}
                    for key, value in analysis.protected_commitments.items()
                ]
            ),
            hide_index=True,
        )
        st.write("Weak points")
        for point in analysis.weak_points:
            st.write(f"- {point}")

with recommendation_tab:
    st.subheader(recommendation.title)
    st.write("LLM / narrative layer")
    st.caption(f"Provider: {explanation['provider']}")
    info_box(explanation["narrative"])
    st.write(md_safe(f"Amount: **{money(recommendation.amount)} {recommendation.currency}**"))
    st.write(f"Horizon: **{recommendation.horizon_days} days**")
    if recommendation.instrument:
        st.write(
            f"Instrument: **{recommendation.instrument}**, maturity **{recommendation.maturity_days} days**"
        )
    st.write(f"Required approval: **{policy.required_approval}**")
    st.write(f"Market context: {market.market_event}")

    st.write("Ranked options")
    st.dataframe(pd.DataFrame(recommendation.ranked_options), hide_index=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.write("Evidence")
        for item in recommendation.evidence:
            st.write(md_safe(f"- {item}"))
    with c2:
        st.write("Assumptions")
        for item in recommendation.assumptions:
            st.write(md_safe(f"- {item}"))
    with c3:
        st.write("Risks")
        for item in recommendation.risks:
            st.write(md_safe(f"- {item}"))

    st.write("Expected benefit")
    info_box(recommendation.expected_benefit)

with approval_tab:
    st.subheader("Human Approval Boundary")
    st.write(
        "This prototype can retrieve, validate, forecast, diagnose, stress test, and draft recommendations. "
        "It cannot execute investments, borrowing, transfers, FX trades, debt changes, or payment delays."
    )
    st.write(f"Approval required: **{policy.required_approval}**")
    st.write(f"Confidence gate: **{confidence.status}**")

    disabled = confidence.status in {"BLOCK", "REQUEST DATA", "WITHHOLD"} or not policy.passed
    modification = st.text_area("Modification note", placeholder="Optional amount, timing, or follow-up condition")
    a, b, c = st.columns(3)
    if a.button("Approve", disabled=disabled):
        append_audit_record(
            make_audit_record(
                result,
                "human_decision",
                human_decision="approved",
                outcome="Approval recorded only; no financial execution occurred.",
            )
        )
        st.success("Approval recorded. No financial execution occurred.")
    if b.button("Modify", disabled=disabled):
        append_audit_record(
            make_audit_record(
                result,
                "human_decision",
                human_decision=f"modified: {modification or 'No note supplied'}",
                outcome="Modification recorded for treasury review; no financial execution occurred.",
            )
        )
        st.info("Modification recorded for review. No financial execution occurred.")
    if c.button("Reject"):
        append_audit_record(
            make_audit_record(
                result,
                "human_decision",
                human_decision="rejected",
                outcome="Recommendation rejected by human reviewer.",
            )
        )
        st.warning("Rejection recorded.")

with audit_tab:
    st.subheader("Audit Log and Outcome Memory")
    audit = audit_dataframe()
    if audit.empty:
        st.write("No audit records yet.")
    else:
        st.dataframe(audit.sort_values("logged_at", ascending=False), hide_index=True)
    st.caption(f"Audit log path: data/audit_log.jsonl. Currency values are {USD_M}.")
