"""Hybrid lexicon-and-rule estimator for text-only valence, activity, and dominance."""
from dataclasses import dataclass
import math

from .. import config
from ..affect.space import classify_vad
from .intents import detect_intent
from .language import STOPWORDS, identify_language
from .lexicon import load_lexicons, match_clause
from .preprocess import preprocess
from .rules import (
    Contribution,
    adjust_contributions,
    domain_adjustments,
    punctuation_adjustments,
)
from .sarcasm import score_sarcasm


@dataclass
class TextEstimate:
    """A plain-Python affect estimate with evidence for explanation."""

    valence: float
    activity: float
    dominance: float
    confidence: float
    label: str
    label_details: dict
    language: str
    language_confidence: float
    intent: str
    entities: dict
    flags: list
    sarcasm_score: float
    evidence: list

    def as_dict(self):
        return {
            "valence": float(self.valence),
            "activity": float(self.activity),
            "dominance": float(self.dominance),
            "confidence": float(self.confidence),
            "label": self.label,
            "label_details": dict(self.label_details),
            "language": self.language,
            "language_confidence": float(self.language_confidence),
            "intent": self.intent,
            "entities": dict(self.entities),
            "flags": list(self.flags),
            "sarcasm_score": float(self.sarcasm_score),
            "evidence": [dict(item) for item in self.evidence],
        }


def _clamp(value, lower=-1.0, upper=1.0):
    return max(lower, min(upper, float(value)))


def _soft_squash(value):
    return _clamp(math.tanh(value * config.SQUASH_SCALE))


def _weighted_mean(contributions, field):
    denominator = sum(item.weight for item in contributions)
    if not denominator:
        return 0.0
    return sum(getattr(item, field) * item.weight for item in contributions) / denominator


def _label_for(valence, activity, dominance):
    """Choose the closest label prototype in weighted Euclidean V/A/D space.

    Distance is sqrt(dV^2 + dA^2 + LABEL_D_WEIGHT*dD^2); points inside the
    configured neutral radius are labelled neutral regardless of their nearest
    prototype.
    """
    return classify_vad(valence, activity, dominance)["label"]


def _clause_weight(clause, has_contrast):
    if not has_contrast:
        return 1.0
    if clause.follows_contrast:
        return config.CONTRAST_LATER_WEIGHT
    return config.CONTRAST_EARLIER_WEIGHT


def _has_mixed_clauses(clause_values):
    positive = any(
        value >= config.MIXED_EMOTION_MIN_MAGNITUDE for value in clause_values
    )
    negative = any(
        value <= -config.MIXED_EMOTION_MIN_MAGNITUDE for value in clause_values
    )
    return positive and negative


def _confidence(processed, language, language_confidence, contributions, flags):
    """Compute a heuristic confidence score; it is not a calibrated probability.

    Ordinarily, C = (1 - exp(-rate * N)) * L, where N is the contribution
    count and L is language confidence. A supported-language message with
    enough words but no affect contributions starts at neutral_confidence * L,
    even when its support intent is not recognized. With contributions,
    multiply by (1 - agreement_penalty * disagreement) and
    max(unknown_floor, 1 - unknown_penalty * unknown_ratio). Then apply the
    short-text, mixed-language, and sarcasm factors; cap unsupported language
    and clamp C to the configured range.
    """
    words = [token.normalized for token in processed.tokens if token.kind == "word"]
    supported = language in ("en", "pt", "mixed")
    if (
        not contributions
        and len(words) >= config.NEUTRAL_INTENT_MIN_TOKENS
        and supported
    ):
        confidence = config.NEUTRAL_CONFIDENCE * language_confidence
    else:
        evidence = 1.0 - math.exp(
            -config.EVIDENCE_SATURATION_RATE * len(contributions)
        )
        confidence = evidence * language_confidence

    if contributions:
        positive = sum(
            item.weight for item in contributions if item.valence > 0.0
        )
        negative = sum(
            item.weight for item in contributions if item.valence < 0.0
        )
        total = positive + negative
        if total:
            disagreement = min(positive, negative) / total
            confidence *= 1.0 - config.EVIDENCE_AGREEMENT_PENALTY * disagreement

        lexicons = load_lexicons()
        if language == "mixed":
            known_words = set(lexicons.words["en"]) | set(lexicons.words["pt"])
            known_stopwords = set(STOPWORDS["en"]) | set(STOPWORDS["pt"])
        elif language in ("en", "pt"):
            known_words = set(lexicons.words[language])
            known_stopwords = set(STOPWORDS[language])
        else:
            known_words = set()
            known_stopwords = set()
        unknown_count = sum(
            word not in known_words and word not in known_stopwords
            for word in words
        )
        unknown_ratio = unknown_count / float(len(words)) if words else 0.0
        confidence *= max(
            config.UNKNOWN_WORD_CONFIDENCE_FLOOR,
            1.0 - config.UNKNOWN_TOKEN_PENALTY * unknown_ratio,
        )

    if "short_message" in processed.flags:
        confidence *= config.SHORT_CONFIDENCE_FACTOR
    if language == "mixed":
        confidence *= config.MIXED_LANGUAGE_CONFIDENCE_FACTOR
    if "possible_sarcasm" in flags:
        confidence *= config.SARCASM_CONFIDENCE_FACTOR
    if "unsupported_language" in flags:
        confidence = min(confidence, config.UNSUPPORTED_CONFIDENCE_CAP)
    return _clamp(confidence, config.MIN_CONFIDENCE, config.MAX_CONFIDENCE)


def estimate_text(text, context_valence=0.0):
    """Estimate expressed affect with local lexicon evidence and general rules."""
    processed = preprocess(text)
    language, language_confidence, language_flags = identify_language(
        processed.tokens
    )
    intent, entities = detect_intent(processed.original, language)
    lexicons = load_lexicons()

    all_contributions = []
    clause_values = []
    rule_flags = set()
    has_contrast = any(clause.follows_contrast for clause in processed.clauses)
    for clause in processed.clauses:
        lexical_tokens, hits = match_clause(clause, language, lexicons)
        weight = _clause_weight(clause, has_contrast)
        contributions, flags = adjust_contributions(
            lexical_tokens, hits, language, weight
        )
        for contribution in contributions:
            if " " in contribution.term:
                contribution.weight *= config.PHRASE_SALIENCE
            else:
                contribution.weight *= config.WORD_SALIENCE
        all_contributions.extend(contributions)
        rule_flags.update(flags)
        if contributions:
            clause_values.append(
                sum(item.valence for item in contributions)
                / float(len(contributions))
            )

    if language in ("en", "pt") and all_contributions:
        language_confidence = max(
            language_confidence, config.LANG_LEXICON_EVIDENCE_FLOOR
        )

    if _has_mixed_clauses(clause_values):
        rule_flags.add("mixed_emotion")
    if has_contrast:
        rule_flags.add("contrast")

    sarcasm_score = score_sarcasm(
        processed.original,
        all_contributions,
        language,
        context_valence=context_valence,
    )
    if sarcasm_score >= config.SARCASM_THRESHOLD:
        rule_flags.add("possible_sarcasm")
        for contribution in all_contributions:
            if contribution.valence > 0.0:
                contribution.valence *= config.SARCASM_POSITIVE_INVERSION
                contribution.modifiers.append("sarcasm")

    raw_valence = _weighted_mean(all_contributions, "valence")
    raw_activity = (
        _weighted_mean(all_contributions, "activity")
        if all_contributions
        else config.BASELINE_ACTIVITY
    )
    raw_dominance = _weighted_mean(all_contributions, "dominance")

    words = [token.normalized for token in processed.tokens if token.kind == "word"]
    domain_v, domain_a, domain_d, domain_flags = domain_adjustments(
        processed.original, words
    )
    raw_valence += domain_v
    raw_activity += domain_a
    raw_dominance += domain_d
    rule_flags.update(domain_flags)

    raw_valence, punctuation_a, punctuation_flags = punctuation_adjustments(
        processed.original,
        processed.tokens,
        raw_valence,
        "elongation" in processed.flags,
    )
    raw_activity += punctuation_a
    rule_flags.update(punctuation_flags)

    if any(token.kind in ("emoji", "emoticon") for token in processed.tokens):
        rule_flags.add("emoji")
    if not all_contributions:
        rule_flags.add("no_affect_words")

    valence = _soft_squash(raw_valence)
    activity = _soft_squash(raw_activity)
    dominance = _soft_squash(raw_dominance)
    flags = set(processed.flags) | set(language_flags) | rule_flags
    confidence = _confidence(
        processed, language, language_confidence, all_contributions, flags
    )
    if confidence < config.LOW_CONFIDENCE_THRESHOLD:
        flags.add("low_confidence")

    evidence = [
        {
            "term": item.term,
            "contribution": [
                float(item.valence),
                float(item.activity),
                float(item.dominance),
            ],
            "modifiers": list(item.modifiers),
        }
        for item in all_contributions
    ]
    label_details = classify_vad(valence, activity, dominance)
    return TextEstimate(
        valence=float(valence),
        activity=float(activity),
        dominance=float(dominance),
        confidence=float(confidence),
        label=label_details["label"],
        label_details=label_details,
        language=language,
        language_confidence=float(language_confidence),
        intent=intent,
        entities=entities,
        flags=sorted(flags),
        sarcasm_score=float(sarcasm_score),
        evidence=evidence,
    )
