"""Explainable negation, modifier, punctuation, and domain-cue rules."""
from dataclasses import dataclass
import re

from .. import config
from .text_matching import contains_any


@dataclass
class Contribution:
    """One lexicon hit after local modifiers and clause weighting."""

    term: str
    valence: float
    activity: float
    dominance: float
    weight: float
    modifiers: list


def _modifier_before(tokens, start, modifiers):
    matches = []
    for phrase, multiplier in modifiers.items():
        parts = phrase.split()
        if start >= len(parts) and [
            token.normalized for token in tokens[start - len(parts) : start]
        ] == parts:
            matches.append((len(parts), phrase, multiplier))
    if not matches:
        return None
    return max(matches, key=lambda match: (match[0], match[1]))


def _is_negator(word, language):
    if word in config.NEGATORS.get(language, ()):
        return True
    return any(word.endswith(suffix) and len(word) > len(suffix) for suffix in config.NEGATION_SUFFIXES)


def adjust_contributions(tokens, hits, language, clause_weight):
    """Apply short-scope negation, one modifier, capitalization, and weighting."""
    if language == "mixed":
        languages = ("en", "pt")
    elif language in ("en", "pt"):
        languages = (language,)
    else:
        languages = ()

    contributions = []
    flags = set()
    for hit in hits:
        entry = hit.entry
        value_v = entry.valence
        value_a = entry.activity
        value_d = entry.dominance
        modifiers = []

        prior = tokens[max(0, hit.start - config.NEGATION_SCOPE) : hit.start]
        negated = any(
            _is_negator(token.normalized, candidate)
            for candidate in languages
            for token in prior
        )
        if negated:
            value_v *= config.NEGATION_FACTOR
            value_a *= config.NEGATION_ACTIVITY_FACTOR
            modifiers.append("negation")
            flags.add("negation")

        modifier = None
        for candidate in languages:
            chosen = _modifier_before(
                tokens,
                hit.start,
                config.INTENSIFIERS.get(candidate, {}),
            )
            if chosen and (modifier is None or chosen[0] > modifier[0]):
                modifier = chosen
            chosen = _modifier_before(
                tokens,
                hit.start,
                config.DOWNTONERS.get(candidate, {}),
            )
            if chosen and (modifier is None or chosen[0] > modifier[0]):
                modifier = chosen
        if modifier:
            factor = modifier[2]
            value_v *= factor
            value_a *= factor
            value_d *= factor
            modifiers.append(modifier[1])
            flags.add("intensifier" if factor > 1.0 else "downtoner")

        hit_tokens = tokens[hit.start : hit.end]
        if any(
            token.is_upper and len(token.text) >= config.CAPS_MIN_LENGTH
            for token in hit_tokens
        ):
            value_v *= config.CAPS_AMPLIFIER
            value_a *= config.CAPS_AMPLIFIER
            value_d *= config.CAPS_AMPLIFIER
            modifiers.append("caps")
            flags.add("caps")
        contributions.append(
            Contribution(
                term=entry.term,
                valence=value_v,
                activity=value_a,
                dominance=value_d,
                weight=clause_weight,
                modifiers=modifiers,
            )
        )
    return contributions, sorted(flags)


def domain_adjustments(text, words):
    """Return message-level VAD adjustments and flags from support-domain cues."""
    normalized = text.lower()
    word_set = set(words)
    valence = 0.0
    activity = 0.0
    dominance = 0.0
    flags = set()

    negative_event = contains_any(normalized, config.DOMAIN_NEGATIVE_TERMS)
    if negative_event:
        valence += config.DOMAIN_PROBLEM_VALENCE
        flags.add("negative_event")
    issue_context = negative_event or bool(
        word_set.intersection(("wait", "waiting", "pending", "refund", "order", "broken"))
    )
    repeated = contains_any(normalized, config.REPETITION_CUES) or (
        "still" in word_set and issue_context
    )
    if repeated and issue_context:
        valence += config.REPETITION_VALENCE
        activity += config.REPETITION_ACTIVITY
        flags.add("repeated_issue")

    if contains_any(normalized, config.URGENCY_CUES):
        activity += config.URGENCY_ACTIVITY
        dominance += config.URGENCY_DOMINANCE

    if contains_any(normalized, config.DEMAND_CUES):
        dominance += config.DEMAND_DOMINANCE

    if contains_any(normalized, config.HELPLESSNESS_CUES):
        dominance += config.HELPLESSNESS_DOMINANCE

    if contains_any(normalized, config.PROFANITY_TERMS):
        valence += config.PROFANITY_VALENCE
        activity += config.PROFANITY_ACTIVITY
        flags.add("profanity")

    if contains_any(normalized, config.HUMAN_REQUEST_CUES):
        flags.add("human_request")
    if contains_any(normalized, config.ESCALATION_CUES):
        flags.add("escalation_cue")
    if contains_any(normalized, config.SAFETY_CUES):
        flags.add("safety")

    return valence, activity, dominance, sorted(flags)


def punctuation_adjustments(original, tokens, valence, has_elongation):
    """Use punctuation and caps as modest message-level expression cues."""
    flags = set()
    exclamations = original.count("!")
    question_runs = len(re.findall(r"\?{2,}|\?!+|!\?+", original))
    has_ellipsis = "..." in original or "…" in original
    letters = [token for token in tokens if token.kind == "word"]
    all_caps = bool(letters) and all(token.is_upper for token in letters)
    caps_words = sum(
        token.is_upper and len(token.text) >= config.CAPS_MIN_LENGTH for token in letters
    )

    activity = config.EXCLAMATION_ACTIVITY * exclamations
    activity += config.QUESTION_ACTIVITY * question_runs
    if has_ellipsis:
        activity += config.ELLIPSIS_ACTIVITY
        flags.add("hesitation")
    if caps_words:
        activity += config.CAPS_WORD_ACTIVITY * caps_words
        flags.add("caps")
    if all_caps:
        activity += config.CAPS_MESSAGE_ACTIVITY
    if has_elongation:
        activity += config.ELONGATION_ACTIVITY
    adjusted_valence = valence * (
        1.0 + config.EXCLAMATION_VALENCE_AMPLIFIER * exclamations
    )
    if exclamations:
        flags.add("exclamation")
    if question_runs:
        flags.add("question")
    return adjusted_valence, activity, sorted(flags)
