"""Map NumPy audio features to cautious voice-only affect estimates."""
from dataclasses import dataclass
from functools import lru_cache
import json
import math
from pathlib import Path

from .. import config
from .features import (
    AudioInputError,
    extract_wav_features,
    numpy_available,
)


REFERENCE_STATS_PATH = Path(__file__).with_name("reference_stats.json")


@dataclass
class VoiceEstimate:
    """Voice-only V/A/D estimate with quality features and uncertainty."""

    valence: float
    activity: float
    dominance: float
    confidence: float
    features: dict
    flags: list

    def as_dict(self):
        """Return a compact JSON-serializable voice summary for engine details."""
        selected_features = (
            "duration_seconds",
            "rms_db",
            "snr_db",
            "voiced_ratio",
            "f0_mean_hz",
            "f0_variability",
            "speaking_rate",
            "spectral_centroid_hz",
            "clipping_ratio",
        )
        return {
            "valence": round(float(self.valence), 3),
            "activity": round(float(self.activity), 3),
            "dominance": round(float(self.dominance), 3),
            "confidence": round(float(self.confidence), 3),
            "features": {
                name: round(float(self.features[name]), 3)
                for name in selected_features
            },
            "flags": list(self.flags),
        }


@lru_cache(maxsize=1)
def _load_reference_stats():
    """Load fixture-derived feature means and standard deviations once."""
    with REFERENCE_STATS_PATH.open("r", encoding="utf-8") as stream:
        return json.load(stream)["statistics"]


def _zscore(value, statistics):
    """Standardize a feature and cap outliers relative to reference data."""
    deviation = max(
        float(statistics["std"]), config.VOICE_REFERENCE_STD_FLOOR
    )
    return max(-3.0, min(3.0, (float(value) - statistics["mean"]) / deviation))


def _confidence(features):
    """Combine clip duration, voicing, SNR, and clipping into confidence."""
    duration_score = min(
        1.0,
        features["duration_seconds"] / config.VOICE_MIN_DURATION_SECONDS,
    )
    voiced_score = min(
        1.0,
        features["voiced_ratio"] / config.VOICE_FULL_VOICED_RATIO,
    )
    snr_span = max(
        config.VOICE_MAX_SNR_DB - config.VOICE_MIN_SNR_DB, 1e-6
    )
    snr_score = max(
        0.0,
        min(
            1.0,
            (features["snr_db"] - config.VOICE_MIN_SNR_DB) / snr_span,
        ),
    )
    clipping_score = max(
        0.0,
        1.0
        - features["clipping_ratio"] * config.VOICE_CLIPPING_PENALTY,
    )
    confidence = (
        config.VOICE_CONFIDENCE_MAX
        * duration_score
        * voiced_score
        * snr_score
        * clipping_score
    )
    if features["no_speech"]:
        return config.MIN_CONFIDENCE
    return max(
        config.MIN_CONFIDENCE,
        min(config.VOICE_CONFIDENCE_MAX, confidence),
    )


def estimate_voice(audio_path):
    """Estimate voice affect; absolute pitch is reported, not used as emotion."""
    if not numpy_available():
        raise AudioInputError("NumPy is unavailable.")
    features = extract_wav_features(audio_path)
    statistics = _load_reference_stats()
    energy_z = _zscore(features["energy_db"], statistics["energy_db"])
    variability_z = _zscore(
        features["f0_variability"], statistics["f0_variability"]
    )
    rate_z = _zscore(
        features["speaking_rate"], statistics["speaking_rate"]
    )
    activity_score = (
        config.VOICE_ACTIVITY_ENERGY_WEIGHT * energy_z
        + config.VOICE_ACTIVITY_PITCH_WEIGHT * variability_z
        + config.VOICE_ACTIVITY_RATE_WEIGHT * rate_z
    )
    activity = math.tanh(activity_score * config.VOICE_ACTIVITY_Z_SCALE)

    # Pitch variability can weakly reflect prosody; mean F0 is excluded because
    # the fixture's low- and high-pitch speakers are both calm.
    valence = 0.10 * math.tanh(variability_z)
    flags = ["no_speech"] if features["no_speech"] else []
    return VoiceEstimate(
        valence=float(max(-0.20, min(0.20, valence))),
        activity=float(max(-1.0, min(1.0, activity))),
        dominance=0.0,
        confidence=float(_confidence(features)),
        features=features,
        flags=flags,
    )
