import unittest

from treasury_advisor.confidence import evaluate_confidence
from treasury_advisor.policy import PolicyResult
from treasury_advisor.quality import DataQualityResult


class ConfidenceGateTests(unittest.TestCase):
    def quality(self, completeness=100.0, freshness=100.0, critical_missing=False):
        return DataQualityResult(
            completeness_score=completeness,
            freshness_score=freshness,
            missing_fields=[],
            stale_days=0,
            consistency_issues=[],
            critical_missing=critical_missing,
            usable=not critical_missing,
        )

    def policy(self, passed=True):
        return PolicyResult(passed=passed, checks=[], required_approval="Treasurer")

    def test_policy_failure_blocks(self):
        result = evaluate_confidence(
            self.quality(),
            self.policy(False),
            forecast_reliability=90,
            market_reliability=90,
            stress_robustness=90,
            traceable=True,
        )

        self.assertEqual(result.status, "BLOCK")
        self.assertEqual(result.score, 0.0)

    def test_critical_missing_requests_data(self):
        result = evaluate_confidence(
            self.quality(completeness=82, freshness=20, critical_missing=True),
            self.policy(True),
            forecast_reliability=80,
            market_reliability=90,
            stress_robustness=80,
            traceable=True,
        )

        self.assertEqual(result.status, "REQUEST DATA")

    def test_high_confidence_recommends(self):
        result = evaluate_confidence(
            self.quality(),
            self.policy(True),
            forecast_reliability=88,
            market_reliability=90,
            stress_robustness=86,
            traceable=True,
        )

        self.assertEqual(result.status, "RECOMMEND")
        self.assertGreaterEqual(result.score, 80)

    def test_medium_confidence_warns(self):
        result = evaluate_confidence(
            self.quality(completeness=76, freshness=72),
            self.policy(True),
            forecast_reliability=68,
            market_reliability=70,
            stress_robustness=60,
            traceable=True,
        )

        self.assertEqual(result.status, "RECOMMEND WITH WARNING")

    def test_low_confidence_requests_data(self):
        result = evaluate_confidence(
            self.quality(completeness=45, freshness=50),
            self.policy(True),
            forecast_reliability=50,
            market_reliability=60,
            stress_robustness=40,
            traceable=False,
        )

        self.assertEqual(result.status, "REQUEST DATA")


if __name__ == "__main__":
    unittest.main()
