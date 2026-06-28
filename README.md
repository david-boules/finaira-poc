# HiveFin: An Agentic Corporate Treasury Advisor PoC

Presentation-ready vertical slice using synthetic corporate treasury data for an arbitrary company.

All data is synthetic / illustrative and not actual company financial data. The prototype does not execute trades, transfers, borrowing, debt changes, payment delays, or FX transactions.

## Run

```bash
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

## Explanation Layer

Ollama is the default explanation provider. Use a local model such as `llama3.2`.

```bash
ollama pull llama3.2
ollama serve
python3 -m streamlit run app.py
```

If Ollama is not running, the app falls back to the deterministic template narrative.

## Test

```bash
python3 -m unittest discover -s tests
```

## What It Demonstrates

- Reproducible synthetic treasury data with fixed random seeds.
- HiveFin glass-box execution UI with visible workflow trace.
- Four selectable scenarios (Scenario 1–4).
- 30/60/90-day cash forecast.
- Genuine investable surplus after protecting reserves, payroll, debt service, planned expansion capex, and a liquidity buffer.
- Hard treasury policy checks.
- Decision Confidence Gate: recommend, warn, request data, withhold, or block.
- Human approval screen for all proposed financial actions.
- JSONL audit log at `data/audit_log.jsonl`.

## Architecture

- `treasury_advisor/synthetic_data.py`: deterministic scenario data.
- `treasury_advisor/quality.py`: freshness, completeness, and consistency checks.
- `treasury_advisor/forecast.py`: baseline 90-day cash projection.
- `treasury_advisor/liquidity.py`: shortfall, surplus, and weak-point analysis.
- `treasury_advisor/market.py`: static market-intelligence adapter.
- `treasury_advisor/policy.py`: hard policy engine.
- `treasury_advisor/confidence.py`: Decision Confidence Gate.
- `treasury_advisor/stress.py`: receivables delay and FX stress test.
- `treasury_advisor/decision.py`: template-based recommendations.
- `treasury_advisor/agent_trace.py`: architecture-aligned agent execution trace for the UI.
- `treasury_advisor/audit.py`: recommendation and human-decision log.
- `treasury_advisor/orchestrator.py`: supervisor workflow.
