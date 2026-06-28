from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


POLICY_DIR = Path("data/policies")


@dataclass(frozen=True)
class RetrievedPolicy:
    title: str
    source: str
    excerpt: str
    score: int


def ensure_policy_documents() -> None:
    POLICY_DIR.mkdir(parents=True, exist_ok=True)
    docs = {
        "treasury_policy.md": """# Synthetic Treasury Policy

Minimum liquidity reserve is USD 300 million. Treasury must protect payroll, debt service, planned expansion capex, and a liquidity buffer before recommending any investment.

Investment, borrowing, FX hedging, cash transfers, debt changes, and payment delays require human approval before execution.

Data older than seven days, missing payroll, missing receivables, or unreconciled cash balances require data remediation before high-impact recommendations are shown.
""",
        "investment_policy.md": """# Synthetic Investment Policy

Allowed short-term instruments are Treasury bills, government money market funds, and insured bank deposits. Maximum maturity is 90 days. Maximum exposure to one counterparty is USD 200 million.

Payroll funds and planned expansion funds cannot be invested.

Investment recommendations should be sized below calculated genuine surplus and should consider stochastic probability of reserve breach.
""",
        "liquidity_strategy.md": """# Synthetic Liquidity Strategy

If projected cash falls below reserve, treasury should preserve cash, accelerate collections, consider short-term financing, and review discretionary outflows before investing surplus.

Stress tests should consider receivables delays, rate moves, and FX pressure.

When Monte Carlo reserve-breach probability is elevated, treasury should prefer preservation, financing readiness, and collections actions over yield pickup.
""",
    }
    for name, content in docs.items():
        path = POLICY_DIR / name
        if not path.exists():
            path.write_text(content.strip() + "\n", encoding="utf-8")


def retrieve_policy_context(query: str, limit: int = 3) -> list[RetrievedPolicy]:
    ensure_policy_documents()
    terms = set(re.findall(r"[a-zA-Z]{4,}", query.lower()))
    results: list[RetrievedPolicy] = []
    for path in POLICY_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        sentences = re.split(r"(?<=[.!?])\s+", text.replace("\n", " "))
        best_sentence = ""
        best_score = 0
        for sentence in sentences:
            sentence_terms = set(re.findall(r"[a-zA-Z]{4,}", sentence.lower()))
            score = len(terms & sentence_terms)
            if score > best_score:
                best_score = score
                best_sentence = sentence
        if best_score:
            title = text.splitlines()[0].replace("#", "").strip()
            results.append(
                RetrievedPolicy(
                    title=title,
                    source=str(path),
                    excerpt=best_sentence,
                    score=best_score,
                )
            )
    return sorted(results, key=lambda item: item.score, reverse=True)[:limit]
