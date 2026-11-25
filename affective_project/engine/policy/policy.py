"""Ordered, explainable policy rules for support actions."""
import re

from .. import config


def _contains_any(text, phrases):
    normalized = str(text).casefold()
    return any(
        re.search(r"(?<!\w)%s(?!\w)" % re.escape(phrase), normalized)
        for phrase in phrases
    )


def _safety(context):
    if "safety" in context["flags"]:
        return (
            "ESCALATE",
            "safety cue detected (V %.2f, A %.2f); route for immediate "
            "human attention"
            % (context["estimate"].valence, context["estimate"].activity),
        )
    return None


def _human_request(context):
    state = context["state"]
    if state["human_declined"] and _contains_any(
        context["text"], config.HUMAN_DECLINED_CUES
    ):
        return None
    if not (
        "human_request" in context["flags"]
        or context["estimate"].intent == "HUMAN_REQUEST"
    ):
        return None
    severe = (
        state["valence"] <= config.ESC_V
        and state["activity"] >= config.ESC_A
    )
    if (
        "escalation_cue" in context["flags"]
        or context["abuse"]
        or state["human_offered_turn"] is not None
        or severe
    ):
        return (
            "ESCALATE",
            "human request with prior offer, urgent cue, abuse, or severe "
            "state (V %.2f, A %.2f)" % (state["valence"], state["activity"]),
        )
    return (
        "OFFER_HUMAN",
        "explicit human request detected (state V %.2f, A %.2f)"
        % (state["valence"], state["activity"]),
    )


def _escalation(context):
    state = context["state"]
    if "escalation_cue" in context["flags"] or context["abuse"]:
        return (
            "ESCALATE",
            "legal, authority, or abuse cue detected (state V %.2f, A %.2f); "
            "urgent human review is safer than an emotion-only response"
            % (state["valence"], state["activity"]),
        )
    if state["severe_streak"] >= config.ESC_TURNS:
        return (
            "ESCALATE",
            "severe state persisted for %d turns (V %.2f <= %.2f, "
            "A %.2f >= %.2f)"
            % (
                state["severe_streak"],
                state["valence"],
                config.ESC_V,
                state["activity"],
                config.ESC_A,
            ),
        )
    if (
        state["neg_streak"] >= config.ESC_NEG_STREAK
        and state["trend"] <= config.TREND_WORSENING_THRESHOLD
    ):
        return (
            "ESCALATE",
            "negative streak %d with worsening trend %.2f"
            % (state["neg_streak"], state["trend"]),
        )
    return None


def _positive_close(context):
    estimate = context["estimate"]
    if (
        estimate.intent == "CLOSING_THANKS"
        and estimate.valence >= config.CLOSE_V
        and "possible_sarcasm" not in context["flags"]
        and (
            not context["state"]["human_declined"]
            or context["state"]["resolved"]
        )
    ):
        return (
            "CLOSE_POSITIVE",
            "closing intent with valence %.2f >= %.2f and no sarcasm flag"
            % (estimate.valence, config.CLOSE_V),
        )
    return None


def _uncertain(context):
    state = context["state"]
    if state["clar_streak"] >= config.MAX_CLARIFY:
        return (
            "OFFER_HUMAN",
            "clarification limit reached after %d consecutive requests"
            % state["clar_streak"],
        )
    if state["acknowledgement_after_empathy"]:
        return None
    if "unsupported_language" in context["flags"]:
        return (
            "ASK_CLARIFICATION",
            "language %s is unsupported or unidentified (confidence %.2f)"
            % (
                context["estimate"].language,
                context["estimate"].confidence,
            ),
        )
    if (
        context["estimate"].confidence < config.CLARIFY_CONF
        and not state["empathy_active"]
        and context["estimate"].valence > config.EMPATHY_MSG_V
    ):
        return (
            "ASK_CLARIFICATION",
            "confidence %.2f is below clarification threshold %.2f"
            % (context["estimate"].confidence, config.CLARIFY_CONF),
        )
    short_ambiguous = (
        context["estimate"].intent == "UNKNOWN"
        and (
            "short_message" in context["flags"]
            or _contains_any(context["text"], config.AMBIGUOUS_CUES)
        )
    )
    if short_ambiguous:
        return (
            "ASK_CLARIFICATION",
            "short or ambiguous message has no useful intent "
            "(confidence %.2f, V %.2f)"
            % (
                context["estimate"].confidence,
                context["estimate"].valence,
            ),
        )
    return None


def _human_offer(context):
    state = context["state"]
    needs_human = (
        state["valence"] <= config.HUMAN_V
        and (
            state["neg_streak"] >= config.HUMAN_STREAK
            or state["trend"] <= config.TREND_WORSENING_THRESHOLD
        )
    ) or state["repeated_issue"]
    if not needs_human:
        return None
    offered_recently = (
        state["human_offer_age"] is not None
        and state["human_offer_age"] <= config.HUMAN_OFFER_COOLDOWN_TURNS
    )
    if state["human_declined"] or offered_recently:
        return (
            "ANSWER_EMPATHIC",
            "human offer was declined or made %s turns ago; avoid repeating it"
            % (
                "unknown"
                if state["human_offer_age"] is None
                else state["human_offer_age"]
            ),
        )
    return (
        "OFFER_HUMAN",
        "persistent or repeated negative issue (state V %.2f, "
        "negative streak %d, trend %.2f)"
        % (state["valence"], state["neg_streak"], state["trend"]),
    )


def _empathy(context):
    estimate = context["estimate"]
    state = context["state"]
    if state["empathy_active"]:
        return (
            "ANSWER_EMPATHIC",
            "empathetic state remains active (state V %.2f, message V %.2f)"
            % (state["valence"], estimate.valence),
        )
    if (
        state["valence"] <= config.EMPATHY_V
        or estimate.valence <= config.EMPATHY_MSG_V
        or (
            estimate.activity >= config.EMPATHY_A
            and estimate.valence < config.EMPATHY_NEGATIVE_V
        )
    ):
        return (
            "ANSWER_EMPATHIC",
            "negative affect warrants empathy (state V %.2f, message V %.2f, "
            "A %.2f)"
            % (state["valence"], estimate.valence, estimate.activity),
        )
    return None


def _default(context):
    return (
        "ANSWER",
        "no higher-priority policy condition matched (V %.2f, A %.2f)"
        % (context["estimate"].valence, context["estimate"].activity),
    )


RULES = (
    ("R0_SAFETY", _safety),
    ("R1_HUMAN_REQUEST", _human_request),
    ("R2_ESCALATE", _escalation),
    ("R3_CLOSE", _positive_close),
    ("R4_UNCERTAIN", _uncertain),
    ("R5_OFFER_HUMAN", _human_offer),
    ("R6_EMPATHY", _empathy),
    ("R7_DEFAULT", _default),
)


def choose_action(estimate, state, text):
    """Return the first action selected by the ordered named rule list."""
    flags = set(estimate.flags) | set(state["flags"])
    abuse = _contains_any(text, config.ABUSE_CUES)
    if abuse:
        flags.add("abuse")
    context = {
        "estimate": estimate,
        "state": state,
        "text": str(text),
        "flags": flags,
        "abuse": abuse,
    }
    for rule_name, rule in RULES:
        decision = rule(context)
        if decision is not None:
            action, reason = decision
            return {
                "action": action,
                "rule": rule_name,
                "reason": reason,
                "flags": sorted(flags),
            }
    raise RuntimeError("The default policy rule did not return an action.")
