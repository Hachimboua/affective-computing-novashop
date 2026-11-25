"""Transparent heuristic sarcasm scoring; context can raise but never decide it."""
import re

from .. import config
from .text_matching import contains_any


_RESOLUTION_CUES = frozenset(("resolved", "fixed", "solved", "resolvido", "resolvida"))


def score_sarcasm(text, contributions, language, context_valence=0.0):
    """Return a bounded heuristic score from idioms, incongruity, and context."""
    normalized = text.lower()
    score = 0.0
    idioms = set(config.SARCASM_IDIOMS.get(language, ()))
    if language == "mixed":
        idioms.update(config.SARCASM_IDIOMS["en"])
        idioms.update(config.SARCASM_IDIOMS["pt"])
    if contains_any(normalized, idioms):
        score = max(score, config.SARCASM_IDIOM_SCORE)

    positive = any(
        item.valence > config.SARCASM_POSITIVE_MIN for item in contributions
    )
    negative_event = contains_any(
        normalized,
        (
            config.SARCASM_NEGATIVE_EVENT_TERMS | config.SARCASM_REPETITION_CUES
        ),
    )
    if positive and negative_event:
        score = max(score, config.SARCASM_INCONGRUITY_SCORE)

    quoted = "|".join(re.escape(term) for term in sorted(config.QUOTED_POSITIVE_TERMS))
    if re.search(r"['\"]\s*(?:%s)\s*['\"]" % quoted, normalized):
        score = max(score, config.SARCASM_QUOTED_SCORE)

    if (
        context_valence <= config.SARCASM_CONTEXT_VALENCE
        and positive
        and not any(cue in normalized for cue in _RESOLUTION_CUES)
    ):
        score = max(score, config.SARCASM_CONTEXT_SCORE)
    return max(0.0, min(1.0, score))
