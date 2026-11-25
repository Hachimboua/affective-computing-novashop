"""Confidence-weighted late fusion for text and optional voice estimates."""
from dataclasses import replace

from .. import config
from .space import clamp, classify_vad


def _blend(
    text_value,
    voice_value,
    text_confidence,
    voice_confidence,
    text_weight,
    voice_weight,
):
    """Blend one dimension using modality weights scaled by confidence."""
    weighted_text = text_weight * text_confidence
    weighted_voice = voice_weight * voice_confidence
    denominator = weighted_text + weighted_voice
    if denominator <= 0.0:
        return float(text_value)
    return clamp(
        (weighted_text * text_value + weighted_voice * voice_value)
        / denominator
    )


def _has_modality_conflict(text_estimate, voice_estimate):
    """Detect strong opposite polarity or positive text with flat prosody."""
    polarity_conflict = (
        text_estimate.valence >= 0.45
        and voice_estimate.valence <= -0.08
    ) or (
        text_estimate.valence <= -0.45
        and voice_estimate.valence >= 0.08
    )
    flat_positive_conflict = (
        text_estimate.valence >= 0.55
        and voice_estimate.activity
        <= config.VOICE_FLAT_ACTIVITY_THRESHOLD
    )
    return polarity_conflict or flat_positive_conflict


def fuse_text_voice(text_estimate, voice_estimate):
    """Return a fused text estimate and whether modalities conflict."""
    text_confidence = float(text_estimate.confidence)
    voice_confidence = float(voice_estimate.confidence)
    valence = _blend(
        text_estimate.valence,
        voice_estimate.valence,
        text_confidence,
        voice_confidence * config.VOICE_VALENCE_CONFIDENCE_FACTOR,
        config.TEXT_VALENCE_WEIGHT,
        config.VOICE_VALENCE_WEIGHT,
    )
    activity = _blend(
        text_estimate.activity,
        voice_estimate.activity,
        text_confidence,
        voice_confidence,
        config.TEXT_ACTIVITY_WEIGHT,
        config.VOICE_ACTIVITY_WEIGHT,
    )
    dominance = _blend(
        text_estimate.dominance,
        voice_estimate.dominance,
        text_confidence,
        voice_confidence,
        config.TEXT_DOMINANCE_WEIGHT,
        config.VOICE_DOMINANCE_WEIGHT,
    )

    conflict = _has_modality_conflict(text_estimate, voice_estimate)
    agreement = max(
        0.0,
        1.0 - abs(text_estimate.valence - voice_estimate.valence) / 2.0,
    )
    confidence = (
        text_confidence * (1.0 - config.VOICE_CONFIDENCE_WEIGHT)
        + voice_confidence * config.VOICE_CONFIDENCE_WEIGHT
        + config.VOICE_AGREEMENT_BONUS * (2.0 * agreement - 1.0)
    )
    if conflict:
        confidence -= config.VOICE_CONFLICT_PENALTY
    confidence = clamp(
        confidence, config.MIN_CONFIDENCE, config.MAX_CONFIDENCE
    )

    sarcasm_score = float(text_estimate.sarcasm_score)
    flags = set(text_estimate.flags)
    flags.add("audio_used")
    flags.update(voice_estimate.flags)
    if conflict:
        flags.add("modality_conflict")
        sarcasm_score = min(
            1.0,
            sarcasm_score + config.SARCASM_MODALITY_CONFLICT_BONUS,
        )
    if sarcasm_score >= config.SARCASM_THRESHOLD:
        flags.add("possible_sarcasm")

    label_details = classify_vad(valence, activity, dominance)
    fused = replace(
        text_estimate,
        valence=float(valence),
        activity=float(activity),
        dominance=float(dominance),
        confidence=float(confidence),
        label=label_details["label"],
        label_details=label_details,
        flags=sorted(flags),
        sarcasm_score=float(sarcasm_score),
    )
    return fused, conflict
