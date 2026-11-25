"""Contract, latency, and error-fallback tests for unusual text inputs."""
import csv
import json
import math
import os
from pathlib import Path
import time
import unittest
from unittest import mock

from engine import config
from engine.engine import Engine
from probes import CONVERSATION_PROBES, PROBE_CASES


_ACTIONS = {
    "ANSWER",
    "ANSWER_EMPATHIC",
    "ASK_CLARIFICATION",
    "OFFER_HUMAN",
    "ESCALATE",
    "CLOSE_POSITIVE",
}
_LABELS = {
    "neutral",
    "calm",
    "joy",
    "anger",
    "frustration",
    "fear",
    "sadness",
}
_RESULT_KEYS = {
    "valence",
    "activity",
    "dominance",
    "confidence",
    "label",
    "action",
    "reply",
    "flags",
    "details",
}
_GENERALIZATION_EXAMPLES = (
    (
        "Could you point me to the current tracking details for shipment 902781?",
        "en",
        "ORDER_STATUS",
    ),
    (
        "The courier delivery is delayed again, and the tracking page is unchanged.",
        "en",
        "DELIVERY_DELAY",
    ),
    (
        "My portable radio stopped working after the first charge.",
        "en",
        "DAMAGED_OR_DEFECTIVE",
    ),
    (
        "I need to send the blender back and request my money back.",
        "en",
        "REFUND_RETURN",
    ),
    (
        "A second invoice charge appeared on my statement without explanation.",
        "en",
        "PAYMENT_BILLING",
    ),
    (
        "I cannot sign in because my password reset link fails.",
        "en",
        "ACCOUNT_LOGIN",
    ),
    (
        "How does the tablet connect to an external display?",
        "en",
        "PRODUCT_QUESTION",
    ),
    ("Great, another charger that broke before I used it.", "en", None),
    (
        "A encomenda 882401 ainda não chegou e o rastreio não muda.",
        "pt",
        "DELIVERY_DELAY",
    ),
    (
        "O carregador não funciona desde a atualização.",
        "pt",
        "DAMAGED_OR_DEFECTIVE",
    ),
    (
        "Quero devolver o tablet e pedir o reembolso da compra.",
        "pt",
        "REFUND_RETURN",
    ),
    (
        "Estou preocupado porque o pagamento do cartão foi cobrado duas vezes.",
        "pt",
        "PAYMENT_BILLING",
    ),
    (
        "Não consigo iniciar sessão na conta desde ontem.",
        "pt",
        "ACCOUNT_LOGIN",
    ),
    (
        "Este monitor é compatível com o computador portátil?",
        "pt",
        "PRODUCT_QUESTION",
    ),
    ("Que maravilha, outra entrega atrasada!", "pt", None),
)


class RobustnessTests(unittest.TestCase):
    def assert_valid_result(self, result, elapsed):
        self.assertEqual(set(result), _RESULT_KEYS)
        for key in ("valence", "activity", "dominance", "confidence"):
            self.assertIs(type(result[key]), float)
            self.assertTrue(math.isfinite(result[key]))
        for key in ("valence", "activity", "dominance"):
            self.assertGreaterEqual(result[key], -1.0)
            self.assertLessEqual(result[key], 1.0)
        self.assertGreaterEqual(result["confidence"], 0.0)
        self.assertLessEqual(result["confidence"], 1.0)
        self.assertIn(result["label"], _LABELS)
        self.assertIn(result["action"], _ACTIONS)
        self.assertIsInstance(result["reply"], str)
        self.assertTrue(result["reply"].strip())
        self.assertIsInstance(result["flags"], list)
        self.assertTrue(all(isinstance(flag, str) for flag in result["flags"]))
        self.assertIsInstance(result["details"], dict)
        json.dumps(result, allow_nan=False)
        self.assertLess(
            elapsed,
            config.TEXT_LATENCY_BUDGET_SECONDS,
            "text processing exceeded the configured latency budget",
        )

    def test_probe_inputs_obey_the_public_contract(self):
        for name, text, kwargs in PROBE_CASES:
            with self.subTest(probe=name):
                engine = Engine()
                started = time.perf_counter()
                result = engine.process(text, **kwargs)
                elapsed = time.perf_counter() - started
                self.assert_valid_result(result, elapsed)

    def test_short_conversations_remain_contract_valid(self):
        for conversation in CONVERSATION_PROBES:
            with self.subTest(turns=len(conversation)):
                engine = Engine()
                for text in conversation:
                    started = time.perf_counter()
                    result = engine.process(text)
                    elapsed = time.perf_counter() - started
                    self.assert_valid_result(result, elapsed)

    def test_phase5_generalization_corpus(self):
        sentences = [text for text, _, _ in _GENERALIZATION_EXAMPLES]
        messages_path = (
            Path(__file__).resolve().parent.parent
            / "engine"
            / "evaluation"
            / "data"
            / "messages.csv"
        )
        with messages_path.open("r", encoding="utf-8", newline="") as stream:
            evaluation_texts = {row["text"] for row in csv.DictReader(stream)}
        self.assertFalse(evaluation_texts.intersection(sentences))
        existing_tests = "\n".join(
            path.read_text(encoding="utf-8")
            for path in Path(__file__).resolve().parent.glob("*.py")
            if path.resolve() != Path(__file__).resolve()
        )
        self.assertFalse(any(text in existing_tests for text in sentences))

        for index, (text, language, intent) in enumerate(
            _GENERALIZATION_EXAMPLES, 1
        ):
            with self.subTest(case=index):
                result = Engine().process(text)
                self.assertEqual(result["details"]["lang"], language)
                self.assertNotIn("unsupported_language", result["flags"])
                if intent:
                    self.assertEqual(result["details"]["intent"], intent)
                if index in (8, 15):
                    self.assertIn("possible_sarcasm", result["flags"])
                    self.assertLess(result["valence"], 0.0)

    def test_internal_error_returns_an_explicit_contract_fallback(self):
        with mock.patch.dict(os.environ, {"ENGINE_STRICT": "0"}):
            with mock.patch(
                "engine.engine.estimate_text", side_effect=ValueError("broken")
            ):
                result = Engine().process("A safe, new test message.")

        self.assertEqual(result["valence"], 0.0)
        self.assertEqual(result["activity"], 0.0)
        self.assertEqual(result["dominance"], 0.0)
        self.assertEqual(result["confidence"], 0.05)
        self.assertEqual(result["label"], "neutral")
        self.assertEqual(result["action"], "ASK_CLARIFICATION")
        self.assertIn("internal_error", result["flags"])
        self.assertEqual(result["details"]["error_type"], "ValueError")
        self.assert_valid_result(result, 0.0)

    def test_engine_strict_reraises_internal_errors(self):
        with mock.patch.dict(os.environ, {"ENGINE_STRICT": "1"}):
            with mock.patch(
                "engine.engine.estimate_text", side_effect=ValueError("broken")
            ):
                with self.assertRaisesRegex(ValueError, "broken"):
                    Engine().process("A second safe test message.")


if __name__ == "__main__":
    unittest.main()
