import unittest

from treasury_advisor.orchestrator import run_scenario


class AgentTraceTests(unittest.TestCase):
    def test_trace_contains_architecture_agents(self):
        result = run_scenario("healthy_surplus")
        agents = [step["agent"] for step in result["agent_trace"]]

        self.assertIn("Scope Guardrail", agents)
        self.assertIn("Data Quality Guardrail", agents)
        self.assertIn("Cashflow Forecast Agent", agents)
        self.assertIn("Grounding Guardrail", agents)
        self.assertIn("Investment Agent", agents)
        self.assertIn("Risk", agents)
        self.assertIn("Decision Confidence Gate", agents)
        self.assertIn("Human-in-the-Loop Checkpoint", agents)


if __name__ == "__main__":
    unittest.main()
