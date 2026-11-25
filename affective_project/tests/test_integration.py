"""Phase 6 integration and compact-log regressions."""
import csv
import json
from pathlib import Path
import unittest

from engine import config
from engine.engine import Engine
from harness.logger import format_entry
from harness.session import Session


GENERALIZATION_CASES = (
    ("Could you tell me how to follow the parcel's route?", "en"),
    ("My headphones still charge correctly after the update.", "en"),
    ("Please show me where the invoice is stored in the account.", "en"),
    ("I need a warranty explanation for this smart speaker.", "en"),
    ("The parcel was rerouted, and I want to know its new arrival estimate.", "en"),
    ("I changed the password and can open my profile again.", "en"),
    ("Can a tablet sleeve be cleaned with a damp cloth?", "en"),
    ("My return label is ready, but the collection time is unclear.", "en"),
    ("Pode dizer-me como acompanho a rota da encomenda?", "pt"),
    ("Os meus auscultadores carregam normalmente depois da atualização.", "pt"),
    ("Eu só quero saber onde encontro a fatura que está guardada na minha conta.", "pt"),
    ("Preciso de uma explicação sobre a garantia desta coluna inteligente.", "pt"),
    ("A encomenda mudou de rota e quero saber a nova previsão.", "pt"),
    ("Mudei a palavra-passe e já consigo abrir o meu perfil.", "pt"),
    ("Esta capa de tablet pode ser limpa com um pano húmido?", "pt"),
)


class IntegrationTests(unittest.TestCase):
    def test_fresh_language_and_log_generalization_cases(self):
        sentences = [text for text, _ in GENERALIZATION_CASES]
        root = Path(__file__).resolve().parent.parent
        messages_path = root / "engine" / "evaluation" / "data" / "messages.csv"
        with messages_path.open("r", encoding="utf-8", newline="") as stream:
            evaluation_texts = {row["text"] for row in csv.DictReader(stream)}
        self.assertFalse(evaluation_texts.intersection(sentences))
        existing_tests = "\n".join(
            path.read_text(encoding="utf-8")
            for path in Path(__file__).resolve().parent.glob("*.py")
            if path.resolve() != Path(__file__).resolve()
        )
        self.assertFalse(any(text in existing_tests for text in sentences))

        for index, (text, expected_language) in enumerate(
            GENERALIZATION_CASES, 1
        ):
            with self.subTest(case=index):
                entry = Session(Engine(), log=False).send(text)
                details = entry["details"]
                self.assertEqual(details["lang"], expected_language)
                self.assertIn("state", details)
                self.assertIn("rule", details)
                self.assertIn("timing_ms", details)
                self.assertEqual(
                    set(details["timing_ms"]),
                    {"text", "state", "policy_reply", "total"},
                )
                self.assertTrue(
                    all(value >= 0 for value in details["timing_ms"].values())
                )
                self.assertEqual(
                    len(details["evidence"]),
                    min(
                        details["evidence_count"],
                        config.DETAILS_EVIDENCE_LIMIT,
                    ),
                )
                json.dumps(entry, allow_nan=False)
                detail_lines = [
                    line
                    for line in format_entry(entry).splitlines()
                    if line.startswith("DETAILS    :")
                ]
                self.assertEqual(len(detail_lines), 1)
                self.assertLessEqual(len(detail_lines[0]), 650)

    def test_long_evidence_is_capped_in_log_details(self):
        entry = Session(Engine(), log=False).send("good " * 2500)
        details = entry["details"]
        self.assertGreater(
            details["evidence_count"], config.DETAILS_EVIDENCE_LIMIT
        )
        self.assertEqual(
            len(details["evidence"]), config.DETAILS_EVIDENCE_LIMIT
        )
        detail_line = next(
            line
            for line in format_entry(entry).splitlines()
            if line.startswith("DETAILS    :")
        )
        self.assertLessEqual(len(detail_line), 650)


if __name__ == "__main__":
    unittest.main()
