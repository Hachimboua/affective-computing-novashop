"""Confidence-weighted conversation state and recent-turn signals."""
import re

from .. import config


def _contains_any(text, phrases):
    return any(
        re.search(r"(?<!\w)%s(?!\w)" % re.escape(phrase), text)
        for phrase in phrases
    )


def _slope(values):
    """Return the least-squares slope of a short sequence of values."""
    if len(values) < 2:
        return 0.0
    mean_x = (len(values) - 1) / 2.0
    mean_y = sum(values) / float(len(values))
    denominator = sum((index - mean_x) ** 2 for index in range(len(values)))
    if not denominator:
        return 0.0
    numerator = sum(
        (index - mean_x) * (value - mean_y)
        for index, value in enumerate(values)
    )
    return numerator / denominator


class StateTracker:
    """Track smoothed affect and bounded conversation history."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Restore the initial state for a new conversation."""
        self.state = None
        self.history = []
        self.turn_count = 0
        self.empathy_active = False
        self.human_declined = False
        self.escalated = False
        self.resolved = False

    @property
    def context_valence(self):
        """Return smoothed valence for context-sensitive perception."""
        return self.state["valence"] if self.state is not None else 0.0

    def _smooth(self, estimate):
        values = (
            float(estimate.valence),
            float(estimate.activity),
            float(estimate.dominance),
        )
        if self.state is None:
            self.state = {
                "valence": values[0],
                "activity": values[1],
                "dominance": values[2],
            }
        else:
            rate = config.STATE_ALPHA * float(estimate.confidence)
            for key, value in zip(
                ("valence", "activity", "dominance"), values
            ):
                self.state[key] += rate * (value - self.state[key])

    def begin_turn(self, estimate, text):
        """Update affect state and return signals for the policy to evaluate."""
        self._smooth(estimate)
        self.turn_count += 1
        normalized = str(text).casefold()
        prior_history = self.history[:]
        previous = prior_history[-1] if prior_history else None
        previous_action = previous["action"] if previous else None
        current_resolved = _contains_any(normalized, config.RESOLUTION_CUES)
        if (
            estimate.intent == "CLOSING_THANKS"
            and estimate.valence >= config.CLOSE_V
        ):
            current_resolved = True
        self.resolved = self.resolved or current_resolved

        offers = [
            item["turn"]
            for item in prior_history
            if item["action"] == "OFFER_HUMAN"
        ]
        human_offered_turn = offers[-1] if offers else None
        if (
            human_offered_turn is not None
            and _contains_any(normalized, config.HUMAN_DECLINED_CUES)
        ):
            self.human_declined = True

        record = {
            "turn": self.turn_count,
            "valence": float(estimate.valence),
            "activity": float(estimate.activity),
            "dominance": float(estimate.dominance),
            "confidence": float(estimate.confidence),
            "label": estimate.label,
            "intent": estimate.intent,
            "action": None,
            "flags": sorted(set(estimate.flags)),
            "state_valence": float(self.state["valence"]),
            "state_activity": float(self.state["activity"]),
            "state_dominance": float(self.state["dominance"]),
        }
        self.history.append(record)
        self.history = self.history[-config.STATE_HISTORY_SIZE :]

        recent = self.history[-config.STATE_TREND_WINDOW :]
        trend = _slope([item["valence"] for item in recent])
        neg_streak = 0
        for item in reversed(self.history):
            if item["valence"] < config.NEG_TURN_V:
                neg_streak += 1
            else:
                break

        severe_streak = 0
        for item in reversed(self.history):
            if (
                item["state_valence"] <= config.ESC_V
                and item["state_activity"] >= config.ESC_A
            ):
                severe_streak += 1
            else:
                break

        clarification_streak = 0
        for item in reversed(prior_history):
            if item["action"] == "ASK_CLARIFICATION":
                clarification_streak += 1
            else:
                break

        negative_intent_count = sum(
            item["intent"] == estimate.intent
            and item["valence"] < config.NEG_TURN_V
            for item in self.history
        )
        repeated_issue = (
            estimate.intent != "UNKNOWN"
            and negative_intent_count >= config.REPEATED_ISSUE_MIN
        )
        flags = set(record["flags"])
        if repeated_issue:
            flags.add("repeated_issue")
        if trend <= config.TREND_WORSENING_THRESHOLD:
            flags.add("trend_worsening")
        if self.human_declined:
            flags.add("human_declined")
        record["flags"] = sorted(flags)

        if self.empathy_active and self.state["valence"] > config.EMPATHY_EXIT_V:
            self.empathy_active = False
        if (
            self.state["valence"] <= config.EMPATHY_V
            or estimate.valence <= config.EMPATHY_MSG_V
            or (
                estimate.activity >= config.EMPATHY_A
                and estimate.valence < config.EMPATHY_NEGATIVE_V
            )
        ):
            self.empathy_active = True

        human_offer_age = (
            self.turn_count - human_offered_turn
            if human_offered_turn is not None
            else None
        )
        acknowledgement_after_empathy = (
            previous_action == "ANSWER_EMPATHIC"
            and _contains_any(normalized, config.ACKNOWLEDGMENT_CUES)
        )
        return {
            "turn": self.turn_count,
            "valence": float(self.state["valence"]),
            "activity": float(self.state["activity"]),
            "dominance": float(self.state["dominance"]),
            "trend": float(trend),
            "neg_streak": neg_streak,
            "peak_negative": min(
                item["valence"] for item in self.history
            ),
            "clar_streak": clarification_streak,
            "severe_streak": severe_streak,
            "human_offered_turn": human_offered_turn,
            "human_offer_age": human_offer_age,
            "human_declined": bool(self.human_declined),
            "escalated": bool(self.escalated),
            "repeated_issue": bool(repeated_issue),
            "resolved": bool(self.resolved),
            "empathy_active": bool(self.empathy_active),
            "previous_action": previous_action,
            "acknowledgement_after_empathy": acknowledgement_after_empathy,
            "flags": sorted(flags),
        }

    def record_action(self, action):
        """Attach the selected action to the current history record."""
        if not self.history:
            raise RuntimeError("begin_turn must be called before record_action.")
        self.history[-1]["action"] = action
        if action == "OFFER_HUMAN":
            self.human_declined = False
        if action == "ESCALATE":
            self.escalated = True

    def history_snapshot(self):
        """Return copies of recent turn data for JSON-serializable details."""
        return [dict(item) for item in self.history]
