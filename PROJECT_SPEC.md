# Corporate Treasury Advisor PoC — Project Specification

## 1. One-sentence product definition
An Agentic AI Treasury Advisor that forecasts liquidity, understands company goals, monitors external market conditions, and recommends how to preserve, invest, finance, or optimize cash while enforcing company policies and requiring human approval.

## 2. Business problem
Corporate treasury decisions are fragmented across spreadsheets, ERP data, bank balances, policy documents, market feeds, and human judgment. Liquidity risks are often discovered too late, while genuine surplus cash can remain idle. The prototype should show how a controlled agentic system can combine those inputs into proactive, explainable, policy-compliant recommendations.

## 3. Target user
Primary user: Corporate Treasurer.
Secondary users: Treasury analyst, CFO, auditor.

## 4. End-to-end workflow
1. Trigger: user question, scheduled daily run, or market event.
2. Scope check: reject non-treasury requests.
3. Data retrieval:
   - Internal structured data: bank balances, AR/AP, payroll, debt, capex, expansion plans.
   - External structured data: rates, FX, short-term yields.
   - Unstructured context: treasury policy, investment rules, goals, covenants.
4. Data-quality check.
5. Cash-flow forecast.
6. Liquidity and working-capital diagnosis.
7. Market-condition interpretation.
8. Capital-allocation option comparison.
9. Deterministic financial calculations and stress tests.
10. Policy rules check.
11. Decision Confidence Gate.
12. Recommendation explanation.
13. Human approval / modification / rejection.
14. Audit and outcome tracking.

## 5. Components

### Supervisor / Orchestrator
Routes the workflow and ensures checks happen in the correct order.

### Data Quality & Context Module
Checks missing fields, stale timestamps, inconsistent totals, and retrieves company goals and policy context.

### Cash-Flow Forecasting Module
Produces 30/60/90-day projected cash balances with a simple uncertainty range.

### Liquidity & Working-Capital Module
Finds:
- projected shortfalls
- genuine surplus above minimum reserve and planned commitments
- delayed receivables
- concentrated payables
- idle cash
- FX mismatches

### Market Intelligence Module
Uses mock/static market inputs for:
- interest rate
- short-term investment yield
- borrowing rate
- FX rate
- optional market event

### Capital Allocation Engine
Ranks actions:
- preserve cash
- invest genuine surplus
- repay debt
- arrange financing
- improve collections
- renegotiate payment timing
- hedge FX

### Deterministic Tools
- investable-surplus calculator
- financing-cost calculator
- return calculator
- liquidity-ratio calculator
- scenario simulator
- stress-test calculator

### Policy Engine
Example hard rules:
- Minimum reserve: configurable.
- Payroll funds cannot be invested.
- Planned capex within the horizon must be protected.
- Maximum investment maturity: configurable.
- Maximum amount per counterparty: configurable.
- Only allowed instruments may be recommended.
- High-value actions require CFO approval.

### Decision Confidence Gate
Inputs:
- data completeness score
- data freshness score
- forecast reliability score
- market-data reliability score
- policy pass/fail
- stress-test robustness score
- output traceability pass/fail

Example logic:
- Policy fail -> BLOCK
- Critical data missing -> REQUEST DATA
- Confidence >= 80 -> RECOMMEND
- Confidence 60–79 -> RECOMMEND WITH WARNING
- Confidence < 60 -> WITHHOLD

### Recommendation Layer
Every recommendation must show:
- action
- amount
- currency
- horizon
- evidence
- assumptions
- expected benefit
- risks
- confidence
- required approval
- source timestamps

### Human Approval Boundary
System may autonomously retrieve, validate, forecast, diagnose, simulate, alert, and draft recommendations.

System may not autonomously execute investments, borrowing, cash transfers, FX trades, debt changes, or payment delays.

### Audit / Memory
Store:
- request
- data timestamps
- tool outputs
- assumptions
- recommendation
- policy results
- confidence result
- human decision
- actual outcome

## 6. Synthetic data design
Create at least 18 months of daily or weekly observations using a fixed seed.

### Suggested fields
- date
- opening_cash
- customer_receipts
- other_inflows
- supplier_payments
- payroll
- operating_expenses
- debt_service
- capex
- fx_payments
- closing_cash
- ar_due
- ap_due
- data_updated_at

### Patterns to simulate
- recurring payroll
- weekly/monthly seasonality
- growth trend
- occasional large supplier payments
- delayed receivables
- planned expansion payment
- FX-denominated obligation
- one stress period

Use generated data primarily for the demo. Training a sophisticated model is not required.

## 7. Demo scenarios

### Scenario A — Healthy surplus
- Forecast remains above reserve.
- Expansion funds are protected.
- Some cash is genuinely surplus.
- Policy and stress tests pass.
- Recommend a bounded short-term investment.
- Human approval required.

### Scenario B — Liquidity shortfall
- Forecast falls below reserve in 45–60 days.
- Root cause: delayed receivables plus planned capex.
- Recommend collections action, financing, or delayed discretionary spend.
- No investment recommendation unless separate protected surplus exists.

### Scenario C — Guardrail block
- AR data is stale or payroll is missing.
- Confidence falls below threshold.
- System withholds recommendation and requests the exact missing data.

### Scenario D — Stress shock
- Receivables delayed by 15 days, rates +200 bps, or FX depreciates 10%.
- Show how the preferred action changes.

## 8. Streamlit screens

### Dashboard
- Synthetic-data banner
- Current cash
- 30/60/90-day projected cash
- Minimum reserve
- Genuine surplus / shortfall
- Confidence score
- Primary alert

### Analysis
- Forecast chart
- inflow/outflow breakdown
- identified weak points
- stress-test controls

### Recommendation
- ranked options
- recommended action
- amount and timing
- expected benefit
- risks and assumptions
- policy checks
- confidence decision

### Approval
- Approve
- Modify
- Reject
- Require CFO approval when threshold exceeded

### Audit
- prior runs
- data timestamps
- recommendations
- human decisions
- outcomes

## 9. Acceptance criteria
The prototype is complete when:
- It runs locally with a documented command.
- Synthetic data is generated reproducibly.
- The dashboard shows 30/60/90-day projections.
- At least four scenarios can be selected.
- Policy checks visibly pass or fail.
- The confidence gate can allow, warn, request data, and block.
- No financial action executes automatically.
- Every recommendation shows evidence, assumptions, risks, and approval requirements.
- An audit record is created for each run.
- Tests cover the policy engine and confidence gate.

## 10. Build priority
1. Working vertical slice.
2. Guardrail scenarios.
3. Clear UI and charts.
4. Audit trail.
5. Optional LLM-generated narrative.
6. Optional RAG.
7. Optional live market API.

The prototype should still work fully without an LLM API key by using template-based explanations.
