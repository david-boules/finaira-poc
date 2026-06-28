import unittest

from treasury_advisor.config import SCENARIOS
from treasury_advisor.forecast_models import fit_statistical_forecast
from treasury_advisor.llm_adapter import generate_explanation
from treasury_advisor.orchestrator import run_scenario
from treasury_advisor.rag import retrieve_policy_context
from treasury_advisor.simulation import run_monte_carlo
from treasury_advisor.synthetic_data import load_scenario_data, ensure_synthetic_data


class NewModuleTests(unittest.TestCase):
    def setUp(self):
        ensure_synthetic_data()

    def test_statistical_forecast_and_monte_carlo(self):
        df = load_scenario_data("healthy_surplus")
        result = run_scenario("healthy_surplus")
        forecast = fit_statistical_forecast(df)
        simulation = run_monte_carlo(forecast, result["analysis"].current_cash, n_simulations=100)

        self.assertEqual(len(forecast.frame), 90)
        self.assertGreaterEqual(forecast.backtest.reliability_score, 50)
        self.assertEqual(simulation.simulation_count, 100)
        self.assertGreaterEqual(simulation.probability_reserve_breach, 0)

    def test_rag_retrieves_policy_context(self):
        results = retrieve_policy_context("investment surplus reserve maturity approval")

        self.assertTrue(results)
        self.assertIn("Policy", results[0].title)

    def test_llm_adapter_template_fallback(self):
        result = run_scenario(next(iter(SCENARIOS)))
        explanation = generate_explanation(
            {
                "recommendation": result["recommendation"],
                "confidence": result["confidence"],
                "analysis": result["analysis"],
                "simulation": result["simulation"],
            },
            result["policy_context"],
        )

        self.assertIn("provider", explanation)
        self.assertTrue(explanation["narrative"])


if __name__ == "__main__":
    unittest.main()
