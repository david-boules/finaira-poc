import unittest

from treasury_advisor.config import POLICY
from treasury_advisor.policy import evaluate_policy


class PolicyEngineTests(unittest.TestCase):
    def test_investment_cannot_exceed_genuine_surplus(self):
        recommendation = {
            "action_type": "invest_surplus",
            "amount": 120.0,
            "instrument": "Treasury bills",
            "maturity_days": 60,
            "requires_human_approval": True,
        }

        result = evaluate_policy(recommendation, investable_surplus=80.0, policy=POLICY)

        self.assertFalse(result.passed)
        failed = [check.name for check in result.checks if not check.passed]
        self.assertIn("Invest only genuine surplus", failed)

    def test_allowed_investment_requires_human_and_cfo_approval(self):
        recommendation = {
            "action_type": "invest_surplus",
            "amount": 125.0,
            "instrument": "Treasury bills",
            "maturity_days": 60,
            "requires_human_approval": True,
        }

        result = evaluate_policy(recommendation, investable_surplus=150.0, policy=POLICY)

        self.assertTrue(result.passed)
        self.assertEqual(result.required_approval, "CFO")

    def test_disallowed_instrument_fails_hard_policy(self):
        recommendation = {
            "action_type": "invest_surplus",
            "amount": 50.0,
            "instrument": "Equity ETF",
            "maturity_days": 60,
            "requires_human_approval": True,
        }

        result = evaluate_policy(recommendation, investable_surplus=100.0, policy=POLICY)

        self.assertFalse(result.passed)
        failed = [check.name for check in result.checks if not check.passed]
        self.assertIn("Allowed instrument", failed)


if __name__ == "__main__":
    unittest.main()
