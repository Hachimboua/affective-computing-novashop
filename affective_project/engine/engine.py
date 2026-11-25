"""Public engine entry point; perception and later phases are composed here."""
from .policy.policy import choose_action
from .policy.replies import render_reply
from .perception.text_estimator import estimate_text
from .state.tracker import StateTracker


class Engine:
    def __init__(self):
        self.reset()

    def reset(self):
        """Start a conversation with no retained message history."""
        self.state_tracker = StateTracker()

    def process(self, text, audio_path=None, image_path=None):
        """Estimate affect, update state, apply policy, and render a reply."""
        estimate = estimate_text(
            text, context_valence=self.state_tracker.context_valence
        )
        state = self.state_tracker.begin_turn(estimate, text)
        decision = choose_action(estimate, state, text)
        action = decision["action"]
        flags = sorted(
            set(estimate.flags) | set(state["flags"]) | set(decision["flags"])
        )
        reply = render_reply(
            action,
            estimate.intent,
            estimate.language,
            state["turn"],
            estimate.entities,
            flags,
        )
        self.state_tracker.record_action(action)
        state_details = dict(state)
        state_details["action"] = action
        state_details["clar_streak"] = (
            state["clar_streak"] + 1
            if action == "ASK_CLARIFICATION"
            else 0
        )
        if action == "OFFER_HUMAN":
            state_details["human_offered_turn"] = state["turn"]
            state_details["human_offer_age"] = 0
            state_details["human_declined"] = False
        if action == "ESCALATE":
            state_details["escalated"] = True
        return {
            "valence": float(estimate.valence),
            "activity": float(estimate.activity),
            "dominance": float(estimate.dominance),
            "confidence": float(estimate.confidence),
            "label": str(estimate.label),
            "action": action,
            "reply": reply,
            "flags": flags,
            "details": {
                "lang": estimate.language,
                "lang_confidence": float(estimate.language_confidence),
                "intent": estimate.intent,
                "entities": dict(estimate.entities),
                "evidence": list(estimate.evidence),
                "sarcasm": float(estimate.sarcasm_score),
                "text": {
                    "v": float(estimate.valence),
                    "a": float(estimate.activity),
                    "d": float(estimate.dominance),
                    "c": float(estimate.confidence),
                },
                "second_label": estimate.label_details["second_label"],
                "label_distance": float(
                    estimate.label_details["label_distance"]
                ),
                "second_distance": (
                    float(estimate.label_details["second_distance"])
                    if estimate.label_details["second_distance"] is not None
                    else None
                ),
                "state": state_details,
                "rule": decision["rule"],
                "reason": decision["reason"],
                "engine_version": "0.3",
            },
        }
