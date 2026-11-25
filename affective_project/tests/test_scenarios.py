"""Pass/fail-only behavior checks against the read-only kit scenarios."""
import json
from pathlib import Path
import unittest

from engine.engine import Engine


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "scenarios"


def _play(relative_path):
    with (SCENARIOS / relative_path).open("r", encoding="utf-8") as stream:
        scenario = json.load(stream)
    engine = Engine()
    return [engine.process(message["text"]) for message in scenario["messages"]]


class ScenarioPolicyTests(unittest.TestCase):
    def test_m1_closes_positive(self):
        results = _play(Path("mandatory") / "M1_calm_faq.json")
        self.assertEqual(results[-1]["action"], "CLOSE_POSITIVE")

    def test_m2_offers_human_then_escalates_on_legal_threat(self):
        results = _play(Path("mandatory") / "M2_growing_frustration.json")
        self.assertTrue(
            any(
                result["action"] in ("OFFER_HUMAN", "ESCALATE")
                for result in results[:-1]
            )
        )
        self.assertEqual(results[-1]["action"], "ESCALATE")
        state_values = [
            result["details"]["state"]["valence"] for result in results
        ]
        self.assertLess(state_values[-1], state_values[0])

    def test_m3_explicit_signals_override_positive_wording(self):
        results = _play(Path("mandatory") / "M3_explicit_requests.json")
        self.assertIn(results[1]["action"], ("OFFER_HUMAN", "ESCALATE"))
        self.assertEqual(results[2]["action"], "ESCALATE")

    def test_m4_clarification_sarcasm_and_portuguese_close(self):
        results = _play(Path("mandatory") / "M4_ambiguity_and_robustness.json")
        self.assertEqual(results[0]["action"], "ASK_CLARIFICATION")
        self.assertIn("possible_sarcasm", results[2]["flags"])
        self.assertNotEqual(results[2]["action"], "CLOSE_POSITIVE")
        self.assertEqual(results[4]["action"], "CLOSE_POSITIVE")
        self.assertIn("Obrigado", results[4]["reply"])

    def test_p1_neutral_questions_get_a_normal_answer(self):
        results = _play(Path("practice") / "P1_refund_neutral.json")
        self.assertIn(results[0]["action"], ("ANSWER", "ANSWER_EMPATHIC"))
        self.assertIn(results[1]["action"], ("ANSWER", "ANSWER_EMPATHIC"))

    def test_p2_uses_empathy_for_low_activity_distress(self):
        results = _play(Path("practice") / "P2_disappointed_customer.json")
        self.assertTrue(
            all(result["action"] == "ANSWER_EMPATHIC" for result in results)
        )
        self.assertTrue(all(result["activity"] < 0.0 for result in results))

    def test_p3_identifies_fear_with_low_dominance(self):
        results = _play(Path("practice") / "P3_anxious_payment.json")
        self.assertEqual(results[1]["label"], "fear")
        self.assertLess(results[1]["dominance"], 0.0)

    def test_p4_negation_has_expected_valence_signs(self):
        results = _play(Path("practice") / "P4_negation_and_praise.json")
        self.assertGreater(results[0]["valence"], 0.0)
        self.assertLess(results[1]["valence"], 0.0)


if __name__ == "__main__":
    unittest.main()
