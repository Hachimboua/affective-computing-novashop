"""STARTER ENGINE - this is the only place your group edits (you may add more files in engine/).

It is intentionally weak: a tiny lexicon, no negation, no rules, no memory of the conversation, no
language handling, and it always answers the same way. Your job is to turn it into a real affective
engine. Keep the contract: process() must return a dict with these keys:

    valence    float in [-1, 1]   negative <-> positive
    activity   float in [-1, 1]   deactivated <-> activated   (also called arousal)
    confidence float in [0, 1]    how much you trust this estimate
    label      str                e.g. neutral, anger, fear, frustration, sadness, joy, calm
    action     str                one of: ANSWER, ANSWER_EMPATHIC, ASK_CLARIFICATION, OFFER_HUMAN,
                                  ESCALATE, CLOSE_POSITIVE
    reply      str                what the assistant says
  optional:
    dominance  float in [-1, 1]   (enables the 3D view of the map)
    flags      list of str        e.g. ["human_request"]
    details    dict               anything useful for the log (it is written to the .txt log)
"""
import re

NEGATIVE = {"bad": -0.5, "terrible": -0.8, "angry": -0.8, "late": -0.4, "unacceptable": -0.8}
POSITIVE = {"thanks": 0.6, "thank": 0.6, "great": 0.7, "good": 0.5, "perfect": 0.8}


class Engine:
    def reset(self):
        """Called at the start of every new conversation."""
        self.history = []

    def process(self, text, audio_path=None, image_path=None):
        words = re.findall(r"[a-z']+", text.lower())
        score = sum(NEGATIVE.get(w, 0) + POSITIVE.get(w, 0) for w in words)
        valence = max(-1.0, min(1.0, score))
        activity = 0.3 if "!" in text else 0.0
        label = "neutral" if abs(valence) < 0.2 else ("joy" if valence > 0 else "frustration")
        self.history.append(valence)
        return {"valence": valence, "activity": activity, "confidence": 0.3, "label": label,
                "action": "ANSWER", "reply": "Thanks for your message. How can I help?",
                "flags": [], "details": {"words": len(words)}}
