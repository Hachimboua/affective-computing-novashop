"""Focused tests for optional voice features, fusion, and fallback behavior."""
import csv
import math
from pathlib import Path
import random
import struct
import tempfile
import unittest
import wave
from unittest.mock import patch

from engine import config
from engine.affect.fusion import fuse_text_voice
from engine.engine import Engine
from engine.perception.text_estimator import estimate_text
from engine.voice.features import extract_features, numpy_available, read_wav
from engine.voice.voice_estimator import (
    VoiceEstimate,
    _confidence,
    estimate_voice,
)


ROOT = Path(__file__).resolve().parent.parent
AUDIO_DIR = ROOT / "assets" / "audio"
GENERALIZATION_CASES = (
    ("My charger keeps disconnecting whenever I move the cable.", "en"),
    ("The checkout page froze before I could confirm my basket.", "en"),
    ("I cannot locate the serial number on this appliance.", "en"),
    ("The replacement filter fits the older vacuum model.", "en"),
    ("Please email the warranty terms before the technician visits.", "en"),
    ("My headphones pair with the laptop but not the phone.", "en"),
    ("Could you explain why the discount vanished at payment?", "en"),
    ("The parcel locker code expired while I was travelling.", "en"),
    ("A aplicação fecha quando tento consultar o recibo.", "pt"),
    ("O carregador aquece demasiado durante a utilização.", "pt"),
    ("Não consigo associar este comando à televisão.", "pt"),
    ("A tampa não encaixa bem no modelo mais recente.", "pt"),
    ("Podem enviar as condições da garantia por correio eletrónico?", "pt"),
    ("A página de pagamento bloqueou antes de concluir a compra.", "pt"),
    ("Quero alterar a morada de entrega antes da recolha.", "pt"),
)


def _write_wav(path, samples, sample_rate=16000, channels=1):
    """Write normalized mono/stereo samples as signed 16-bit PCM."""
    interleaved = []
    for sample in samples:
        value = max(-1.0, min(1.0, float(sample)))
        encoded = int(round(value * 32767))
        interleaved.extend([encoded] * channels)
    with wave.open(str(path), "wb") as stream:
        stream.setnchannels(channels)
        stream.setsampwidth(2)
        stream.setframerate(sample_rate)
        stream.writeframes(struct.pack("<%dh" % len(interleaved), *interleaved))


def _without_timing(result):
    comparable = dict(result)
    comparable["details"] = dict(result["details"])
    comparable["details"].pop("timing_ms")
    return comparable


@unittest.skipUnless(numpy_available(), "optional NumPy dependency is absent")
class VoiceFeatureTests(unittest.TestCase):
    def test_synthetic_tone_pitch_and_noise_rejection(self):
        import numpy as np

        sample_rate = 16000
        tone = [
            0.2 * math.sin(2.0 * math.pi * 200.0 * index / sample_rate)
            for index in range(sample_rate)
        ]
        tone_features = extract_features(np.asarray(tone), sample_rate)
        self.assertAlmostEqual(tone_features["f0_mean_hz"], 200.0, delta=5.0)
        self.assertGreater(tone_features["voiced_ratio"], 0.8)

        generator = random.Random(42)
        noise = [
            generator.uniform(-0.3, 0.3) for _ in range(sample_rate * 2)
        ]
        noise_features = extract_features(np.asarray(noise), sample_rate)
        self.assertLess(noise_features["voiced_ratio"], 0.1)
        self.assertTrue(noise_features["no_speech"])

    def test_silence_is_marked_as_no_speech(self):
        import numpy as np

        features = extract_features(np.zeros(16000), 16000)
        self.assertTrue(features["no_speech"])
        self.assertEqual(features["voiced_ratio"], 0.0)

    def test_fixture_confidence_activity_and_pitch_normalization(self):
        calm = estimate_voice(AUDIO_DIR / "calm_clean.wav")
        calm_noisy = estimate_voice(AUDIO_DIR / "calm_noisy.wav")
        agitated = estimate_voice(AUDIO_DIR / "agitated_clean.wav")
        agitated_noisy = estimate_voice(AUDIO_DIR / "agitated_noisy.wav")
        low_pitch = estimate_voice(AUDIO_DIR / "speaker_low.wav")
        high_pitch = estimate_voice(AUDIO_DIR / "speaker_high.wav")

        self.assertLess(calm_noisy.confidence, calm.confidence)
        self.assertGreater(agitated.activity, calm.activity)
        self.assertGreater(agitated_noisy.activity, calm_noisy.activity)
        self.assertLess(abs(high_pitch.activity - low_pitch.activity), 0.20)

    def test_confidence_penalizes_duration_voicing_noise_and_clipping(self):
        baseline = {
            "duration_seconds": 2.0,
            "voiced_ratio": 0.5,
            "snr_db": 20.0,
            "clipping_ratio": 0.0,
            "no_speech": False,
        }
        baseline_confidence = _confidence(baseline)
        for key, value in (
            ("duration_seconds", 0.5),
            ("voiced_ratio", 0.1),
            ("snr_db", -5.0),
            ("clipping_ratio", 0.5),
        ):
            degraded = dict(baseline)
            degraded[key] = value
            with self.subTest(feature=key):
                self.assertLess(_confidence(degraded), baseline_confidence)

    def test_louder_copy_has_higher_activity(self):
        import numpy as np

        samples, sample_rate = read_wav(AUDIO_DIR / "calm_clean.wav")
        louder = np.clip(samples * 4.0, -1.0, 1.0)
        with tempfile.TemporaryDirectory() as directory:
            louder_path = Path(directory) / "louder.wav"
            _write_wav(louder_path, louder, sample_rate)
            self.assertGreater(
                estimate_voice(louder_path).activity,
                estimate_voice(AUDIO_DIR / "calm_clean.wav").activity,
            )

    def test_voice_changes_fused_activity_and_detects_conflict(self):
        text = "That is absolutely fantastic!"
        calm = Engine().process(
            "The manual is available online.",
            audio_path=AUDIO_DIR / "calm_clean.wav",
        )
        agitated = Engine().process(
            "The manual is available online.",
            audio_path=AUDIO_DIR / "agitated_clean.wav",
        )
        self.assertGreater(
            agitated["details"]["fused"]["a"],
            calm["details"]["fused"]["a"],
        )

        text_estimate = estimate_text(text)
        opposing_voice = VoiceEstimate(
            valence=-0.2,
            activity=-0.8,
            dominance=0.0,
            confidence=0.9,
            features={},
            flags=[],
        )
        fused, conflict = fuse_text_voice(text_estimate, opposing_voice)
        self.assertTrue(conflict)
        self.assertIn("modality_conflict", fused.flags)
        self.assertGreater(
            fused.sarcasm_score, text_estimate.sarcasm_score
        )

    def test_stereo_channels_are_averaged_to_mono(self):
        with tempfile.TemporaryDirectory() as directory:
            stereo_path = Path(directory) / "stereo.wav"
            samples = [
                0.2 * math.sin(2.0 * math.pi * 180.0 * i / 16000)
                for i in range(16000)
            ]
            _write_wav(stereo_path, samples, channels=2)
            mono, sample_rate = read_wav(stereo_path)
            self.assertEqual(sample_rate, 16000)
            self.assertEqual(mono.shape, (16000,))


class VoiceIntegrationTests(unittest.TestCase):
    def test_audio_none_preserves_text_only_result(self):
        text = "The charger works well, and I appreciate the quick help."
        text_only = Engine().process(text)
        explicit_none = Engine().process(text, audio_path=None)
        self.assertEqual(
            _without_timing(text_only), _without_timing(explicit_none)
        )
        self.assertIsNone(explicit_none["details"]["voice"])

    def test_missing_and_corrupt_audio_fall_back_to_text(self):
        text = "The parcel arrived safely, thank you."
        text_only = Engine().process(text)
        with tempfile.TemporaryDirectory() as directory:
            missing = Engine().process(
                text, audio_path=Path(directory) / "missing.wav"
            )
            corrupt_path = Path(directory) / "corrupt.wav"
            corrupt_path.write_bytes(b"not a wav file")
            corrupt = Engine().process(text, audio_path=corrupt_path)

        for result in (missing, corrupt):
            self.assertIn("audio_unavailable", result["flags"])
            self.assertEqual(result["valence"], text_only["valence"])
            self.assertEqual(result["label"], text_only["label"])
            self.assertIsNone(result["details"]["voice"])

    def test_unsupported_wav_format_falls_back_to_text(self):
        text = "The charger is working well."
        with tempfile.TemporaryDirectory() as directory:
            unsupported_path = Path(directory) / "eight_bit.wav"
            with wave.open(str(unsupported_path), "wb") as stream:
                stream.setnchannels(1)
                stream.setsampwidth(1)
                stream.setframerate(16000)
                stream.writeframes(b"\x80" * 16000)
            result = Engine().process(text, audio_path=unsupported_path)
        self.assertIn("audio_unavailable", result["flags"])
        self.assertIsNone(result["details"]["voice"])

    def test_missing_numpy_falls_back_to_text(self):
        text = "The order arrived safely."
        with patch("engine.voice.features.np", None):
            result = Engine().process(
                text, audio_path=AUDIO_DIR / "calm_clean.wav"
            )
        self.assertIn("audio_unavailable", result["flags"])
        self.assertIsNone(result["details"]["voice"])

    @unittest.skipUnless(numpy_available(), "optional NumPy dependency is absent")
    def test_silence_is_flagged_in_engine_result(self):
        with tempfile.TemporaryDirectory() as directory:
            silence_path = Path(directory) / "silence.wav"
            _write_wav(silence_path, [0.0] * 16000)
            result = Engine().process(
                "The instruction is clear.", audio_path=silence_path
            )
        self.assertIn("audio_used", result["flags"])
        self.assertIn("no_speech", result["flags"])

    def test_new_bilingual_cases_use_audio_and_expected_language(self):
        messages_path = (
            ROOT / "engine" / "evaluation" / "data" / "messages.csv"
        )
        with messages_path.open(
            "r", encoding="utf-8", newline=""
        ) as stream:
            evaluation_texts = {row["text"] for row in csv.DictReader(stream)}
        sentences = [text for text, _ in GENERALIZATION_CASES]
        self.assertFalse(evaluation_texts.intersection(sentences))
        existing_tests = "\n".join(
            path.read_text(encoding="utf-8")
            for path in Path(__file__).resolve().parent.glob("*.py")
            if path.resolve() != Path(__file__).resolve()
        )
        self.assertFalse(any(text in existing_tests for text in sentences))

        voice_available = config.VOICE_ENABLED and numpy_available()
        for index, (text, expected_language) in enumerate(
            GENERALIZATION_CASES, 1
        ):
            with self.subTest(case=index):
                result = Engine().process(
                    text, audio_path=AUDIO_DIR / "calm_clean.wav"
                )
                self.assertEqual(result["details"]["lang"], expected_language)
                if voice_available:
                    self.assertIn("audio_used", result["flags"])
                    self.assertIsNotNone(result["details"]["voice"])
                    self.assertIn("fused", result["details"])
                    self.assertIn("voice", result["details"]["timing_ms"])
                    self.assertIn("fusion", result["details"]["timing_ms"])
                else:
                    self.assertIn("audio_unavailable", result["flags"])


if __name__ == "__main__":
    unittest.main()
