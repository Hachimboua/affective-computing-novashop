"""Focused tests for conversation state, trends, and hysteresis."""
from types import SimpleNamespace
import unittest

from engine import config
from engine.state.tracker import StateTracker


def _estimate(valence, activity=0.0, dominance=0.0, confidence=1.0, intent="UNKNOWN"):
    return SimpleNamespace(
        valence=valence,
        activity=activity,
        dominance=dominance,
        confidence=confidence,
        label="neutral",
        intent=intent,
        flags=[],
    )


class StateTrackerTests(unittest.TestCase):
    def test_confidence_weighted_ema_initializes_then_smooths(self):
        tracker = StateTracker()
        first = tracker.begin_turn(_estimate(-0.4, 0.2, 0.1), "first")
        tracker.record_action("ANSWER")
        second = tracker.begin_turn(
            _estimate(0.6, -0.2, -0.3, confidence=0.5), "second"
        )
        rate = config.STATE_ALPHA * 0.5
        self.assertAlmostEqual(first["valence"], -0.4)
        self.assertAlmostEqual(second["valence"], -0.4 + rate * 1.0)
        self.assertAlmostEqual(second["activity"], 0.2 + rate * -0.4)
        self.assertAlmostEqual(second["dominance"], 0.1 + rate * -0.4)

    def test_trend_streak_peak_and_repeated_issue(self):
        tracker = StateTracker()
        states = []
        for value in (-0.35, -0.55, -0.70):
            state = tracker.begin_turn(
                _estimate(value, intent="DELIVERY_DELAY"), "delivery delay"
            )
            states.append(state)
            tracker.record_action("ANSWER_EMPATHIC")
        self.assertLess(states[-1]["trend"], 0.0)
        self.assertEqual(states[-1]["neg_streak"], 3)
        self.assertEqual(states[-1]["peak_negative"], -0.70)
        self.assertTrue(states[-1]["repeated_issue"])
        self.assertIn("repeated_issue", states[-1]["flags"])

    def test_clarification_streak_counts_prior_actions(self):
        tracker = StateTracker()
        states = []
        for _ in range(3):
            states.append(tracker.begin_turn(_estimate(0.0), "?"))
            tracker.record_action("ASK_CLARIFICATION")
        self.assertEqual(
            [state["clar_streak"] for state in states],
            [0, 1, 2],
        )

    def test_history_is_bounded_and_records_turn_signals(self):
        tracker = StateTracker()
        for index in range(config.STATE_HISTORY_SIZE + 2):
            tracker.begin_turn(
                _estimate(0.1, intent="PRODUCT_QUESTION"),
                "product question %d" % index,
            )
            tracker.record_action("ANSWER")
        history = tracker.history_snapshot()
        self.assertEqual(len(history), config.STATE_HISTORY_SIZE)
        self.assertEqual(history[-1]["action"], "ANSWER")
        for key in ("valence", "activity", "dominance", "confidence",
                    "label", "intent", "action", "flags"):
            self.assertIn(key, history[-1])

    def test_offer_memory_decline_and_escalation_are_tracked(self):
        tracker = StateTracker()
        tracker.begin_turn(_estimate(-0.3), "concern")
        tracker.record_action("OFFER_HUMAN")
        declined = tracker.begin_turn(_estimate(-0.2), "No thanks, not now.")
        self.assertEqual(declined["human_offered_turn"], 1)
        self.assertEqual(declined["human_offer_age"], 1)
        self.assertTrue(declined["human_declined"])
        tracker.record_action("ESCALATE")
        self.assertTrue(tracker.begin_turn(_estimate(-0.1), "another turn")["escalated"])

    def test_empathy_hysteresis_and_reset(self):
        tracker = StateTracker()
        first = tracker.begin_turn(_estimate(-0.7), "negative")
        self.assertTrue(first["empathy_active"])
        tracker.record_action("ANSWER_EMPATHIC")
        second = tracker.begin_turn(_estimate(0.2), "slightly positive")
        self.assertTrue(second["empathy_active"])
        tracker.record_action("ANSWER_EMPATHIC")
        third = tracker.begin_turn(_estimate(0.9), "strongly positive")
        self.assertFalse(third["empathy_active"])
        tracker.record_action("ANSWER")
        tracker.reset()
        self.assertEqual(tracker.context_valence, 0.0)
        self.assertEqual(tracker.history_snapshot(), [])


if __name__ == "__main__":
    unittest.main()
