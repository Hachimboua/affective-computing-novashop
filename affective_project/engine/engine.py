"""Public engine entry point; perception and later phases are composed here."""
from .perception.text_estimator import estimate_text


class Engine:
    def __init__(self):
        self.reset()

    def reset(self):
        """Start a conversation with no retained message history."""
        self.history = []

    def process(self, text, audio_path=None, image_path=None):
        """Estimate text affect while preserving the starter kit's API."""
        estimate = estimate_text(text)
        self.history.append(estimate.valence)
        return {
            "valence": float(estimate.valence),
            "activity": float(estimate.activity),
            "dominance": float(estimate.dominance),
            "confidence": float(estimate.confidence),
            "label": str(estimate.label),
            "action": "ANSWER",
            "reply": "Thanks for your message. How can I help?",
            "flags": list(estimate.flags),
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
                "engine_version": "0.2",
            },
        }
