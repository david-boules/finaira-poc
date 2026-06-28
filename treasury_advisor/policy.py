from __future__ import annotations

from dataclasses import dataclass

from .config import TreasuryPolicy


@dataclass(frozen=True)
class PolicyCheck:
    name: str
    passed: bool
    severity: str
    message: str


@dataclass(frozen=True)
class PolicyResult:
    passed: bool
    checks: list[PolicyCheck]
    required_approval: str


def evaluate_policy(
    recommendation: dict,
    investable_surplus: float,
    policy: TreasuryPolicy,
) -> PolicyResult:
    checks: list[PolicyCheck] = []
    action = recommendation.get("action_type", "withhold_recommendation")
    amount = float(recommendation.get("amount", 0.0) or 0.0)
    instrument = recommendation.get("instrument")
    maturity_days = int(recommendation.get("maturity_days", 0) or 0)

    checks.append(
        PolicyCheck(
            "Corporate treasury scope",
            action
            in {
                "invest_surplus",
                "arrange_financing",
                "improve_collections",
                "preserve_cash",
                "hedge_fx",
                "withhold_recommendation",
            },
            "hard",
            "Recommendation is limited to corporate treasury actions.",
        )
    )

    if action == "invest_surplus":
        checks.extend(
            [
                PolicyCheck(
                    "Invest only genuine surplus",
                    amount <= investable_surplus and amount > 0,
                    "hard",
                    f"Proposed ${amount:.1f}M must not exceed calculated surplus of ${investable_surplus:.1f}M.",
                ),
                PolicyCheck(
                    "Allowed instrument",
                    instrument in policy.allowed_instruments,
                    "hard",
                    f"{instrument or 'No instrument'} must be in the allowed-instrument list.",
                ),
                PolicyCheck(
                    "Maximum maturity",
                    0 < maturity_days <= policy.max_investment_maturity_days,
                    "hard",
                    f"Maturity must be no more than {policy.max_investment_maturity_days} days.",
                ),
                PolicyCheck(
                    "Counterparty cap",
                    amount <= policy.max_counterparty_amount,
                    "hard",
                    f"Single-counterparty recommendation must not exceed ${policy.max_counterparty_amount:.1f}M.",
                ),
            ]
        )
    elif action == "arrange_financing":
        checks.append(
            PolicyCheck(
                "Financing amount is positive",
                amount > 0,
                "hard",
                "Financing recommendations must specify the amount needed to protect liquidity.",
            )
        )
    elif action == "hedge_fx":
        checks.append(
            PolicyCheck(
                "FX hedge amount is positive",
                amount > 0,
                "hard",
                "FX hedging recommendations must be bounded by measured exposure.",
            )
        )
    elif action == "withhold_recommendation":
        checks.append(
            PolicyCheck(
                "No execution proposed",
                amount == 0,
                "hard",
                "Withheld recommendations cannot include a financial execution amount.",
            )
        )
    else:
        checks.append(
            PolicyCheck(
                "No restricted execution",
                True,
                "hard",
                "No restricted financial execution is proposed.",
            )
        )

    requires_human = action in policy.high_impact_actions and amount > 0
    checks.append(
        PolicyCheck(
            "Human approval boundary",
            recommendation.get("requires_human_approval") == requires_human,
            "hard",
            "Investment, borrowing, transfers, FX trades, debt changes, and payment delays require human approval.",
        )
    )

    required_approval = "None"
    if requires_human:
        required_approval = "CFO" if amount >= policy.cfo_approval_threshold else "Treasurer"

    hard_fail = any(not check.passed and check.severity == "hard" for check in checks)
    return PolicyResult(passed=not hard_fail, checks=checks, required_approval=required_approval)
