import unittest

from treasury_advisor.guardrails import classify_treasury_scope
from treasury_advisor.orchestrator import run_scenario


class GuardrailTests(unittest.TestCase):
    def test_scope_blocks_personal_investment(self):
        result = classify_treasury_scope("Should I buy bitcoin for my retirement portfolio?")

        self.assertFalse(result.in_scope)
        self.assertEqual(result.label, "out_of_scope")

    def test_scope_allows_corporate_treasury(self):
        result = classify_treasury_scope("Assess corporate liquidity and FX hedge needs.")

        self.assertTrue(result.in_scope)

    def test_grounding_manifest_passes_for_scenario(self):
        result = run_scenario("healthy_surplus")

        self.assertTrue(result["grounding"].passed)
        self.assertGreaterEqual(len(result["grounding"].sources), 5)


if __name__ == "__main__":
    unittest.main()
