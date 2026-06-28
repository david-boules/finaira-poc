# AGENTS.md

## Project
Build a fast, presentation-ready proof of concept for an **Agentic AI Corporate Treasury Advisor**.

The prototype is an illustrative Nike case study only. All company data must be clearly labeled **synthetic / illustrative and not actual Nike financial data**.

## Core objective
Demonstrate this end-to-end behavior:

1. Load internal treasury data and company goals.
2. Validate freshness, completeness, and consistency.
3. Forecast 30/60/90-day cash positions.
4. Detect liquidity shortfalls, genuine surplus cash, and working-capital weak points.
5. retrieve relevant external market conditions and company policies.
6. Compare actions: preserve cash, invest true surplus, repay debt, arrange financing, hedge FX, or improve working capital.
7. Enforce hard treasury policies.
8. Run stress tests.
9. Pass the draft through a Decision Confidence Gate.
10. Show, warn, request more data, or block.
11. Require human approval before any financial execution.
12. Record the decision and outcome in an audit log.

## Architecture principle
Do not treat everything as an LLM agent.

- Agents coordinate, reason, and explain.
- Deterministic tools calculate.
- RAG retrieves policies and strategy documents.
- Rules enforce non-negotiable limits.
- Databases store state and audit history.
- Humans approve all high-impact actions.

## MVP stack
Prefer:
- Python
- Streamlit
- pandas / numpy
- scikit-learn or statsmodels for a simple baseline forecast
- Plotly or Streamlit-native charts
- JSON/CSV for synthetic inputs
- SQLite or JSON for audit history

Avoid unnecessary infrastructure. The prototype should run locally with one command.

## Required components
- Supervisor/orchestrator
- Data-quality and context module
- Cash-flow forecast module
- Liquidity and working-capital analysis
- Market-intelligence adapter using mock or static market data
- Capital-allocation decision engine
- Policy rules engine
- Stress-test tool
- Decision Confidence Gate
- Recommendation/explanation layer
- Human approval screen
- Audit log and outcome-memory view

## Required guardrails
- Scope gate: corporate treasury only
- Role/access placeholder
- Data freshness and completeness checks
- No invented numbers
- Hard policy enforcement
- Confidence gate based on measurable evidence
- Human approval required for investment, borrowing, transfers, FX trades, debt changes, or payment delays
- Full audit trail

## Required demo scenarios
1. Healthy surplus: recommend a bounded short-term investment after protecting reserves and planned expansion funds.
2. Liquidity risk: identify a projected shortfall and suggest financing or working-capital actions.
3. Guardrail failure: stale or missing data causes the recommendation to be withheld.
4. Stress test: a receivables delay or FX shock changes the recommendation.

## Synthetic data
Generate reproducible synthetic data with a fixed random seed. Include:
- dates
- opening cash balance
- cash inflows
- cash outflows
- accounts receivable due
- accounts payable due
- payroll
- debt payments
- planned capex / expansion commitments
- currency exposure
- data_updated_at timestamps

Do not claim model accuracy as real-world evidence. The goal is to demonstrate architecture and decision behavior.

## UX expectations
The interface should make the flow understandable to both technical and non-technical judges:
- Summary cards
- 30/60/90-day cash chart
- Surplus/shortfall alert
- Recommended action
- Evidence, assumptions, risks, and confidence
- Policy-check results
- Human approval buttons
- Audit trail
- A visible “synthetic data” banner

## Non-goals
- No real trade execution
- No real bank or Nike integration
- No production security claims
- No autonomous movement of money
- No unsupported financial advice
