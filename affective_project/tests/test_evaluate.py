"""End-to-end check of the evaluation script on a small FIXTURE.

The fixture messages and fixture ratings below are invented test data for
the script only. They are written to a temporary folder, never to
``engine/evaluation/ratings/``, and they are not real SAM ratings.
Run with:  python -m unittest tests.test_evaluate
"""
import csv
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine.evaluation import evaluate  # noqa: E402

FIXTURE_MESSAGES = [
    ("FX-01", "FX1", 1, "dev", "Hello, could you tell me the delivery time for a keyboard?", "fixture", "fixture"),
    ("FX-02", "FX1", 2, "dev", "Great, thank you very much for the help!", "fixture", "fixture"),
    ("FX-03", "FX2", 1, "dev", "My monitor arrived cracked and I am really angry.", "fixture", "fixture"),
    ("FX-04", "FX2", 2, "dev", "I want to talk to a real person now.", "fixture", "fixture"),
    ("FX-05", "FX3", 1, "test", "This message belongs to the test split.", "fixture", "fixture"),
]
# Fixture ratings from two fake raters (FIXTURE_A, FIXTURE_B).
FIXTURE_RATINGS = {
    "FIXTURE_A": [("FX-01", 5, 3, 5, "neutral", "ANSWER"), ("FX-02", 8, 5, 6, "joy", "CLOSE_POSITIVE"),
                  ("FX-03", 2, 8, 6, "anger", "ANSWER_EMPATHIC"), ("FX-04", 3, 7, 6, "anger", "OFFER_HUMAN")],
    "FIXTURE_B": [("FX-01", 6, 3, 5, "neutral", "ANSWER"), ("FX-02", 9, 6, 6, "joy", "CLOSE_POSITIVE"),
                  ("FX-03", 2, 9, 5, "anger", "ANSWER_EMPATHIC"), ("FX-04", 2, 8, 6, "frustration", "OFFER_HUMAN")],
}


def _write_fixture(folder):
    messages = Path(folder) / "messages.csv"
    with open(messages, "w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["msg_id", "conversation_id", "turn", "split", "text", "source", "case_type"])
        writer.writerows(FIXTURE_MESSAGES)
    ratings = Path(folder) / "ratings"
    ratings.mkdir()
    for rater, rows in FIXTURE_RATINGS.items():
        with open(ratings / (rater + ".csv"), "w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["msg_id", "conversation_id", "turn", "rater_id", "valence", "arousal", "dominance", "label", "action", "comment"])
            for msg_id, v, a, d, label, action in rows:
                conversation = msg_id.replace("FX-0", "FX")[:3]
                writer.writerow([msg_id, conversation, 1, rater, v, a, d, label, action, ""])
    return messages, ratings


class EvaluateScriptTests(unittest.TestCase):
    def test_end_to_end_on_fixture(self):
        with tempfile.TemporaryDirectory() as folder:
            messages, ratings = _write_fixture(folder)
            out = Path(folder) / "results"
            code = evaluate.main(["--split", "dev", "--messages", str(messages), "--ratings-dir", str(ratings),
                                  "--out", str(out), "--bootstrap", "50"])
            self.assertEqual(code, 0)
            report = json.loads((out / "dev_metrics.json").read_text(encoding="utf-8"))
            self.assertEqual(set(report["variants"]), {"starter", "full", "no_negation", "no_sarcasm", "no_smoothing"})
            self.assertEqual(report["variants"]["full"]["messages"], 4)
            self.assertEqual(report["agreement"]["raters"], 2)
            self.assertIn("krippendorff_alpha_interval", report["agreement"]["dimensions"]["valence"])
            # Majority vote with a tie (anger vs frustration) excludes FX-04 from label metrics.
            self.assertEqual(report["variants"]["full"]["label"]["ties_excluded"], 1)
            for name in ("dev_summary.md", "dev_predictions.csv", "dev_errors.csv"):
                self.assertTrue((out / name).exists(), name)

    def test_no_ratings_means_no_numbers(self):
        with tempfile.TemporaryDirectory() as folder:
            messages, _ = _write_fixture(folder)
            empty = Path(folder) / "empty_ratings"
            empty.mkdir()
            out = Path(folder) / "results"
            code = evaluate.main(["--split", "dev", "--messages", str(messages), "--ratings-dir", str(empty), "--out", str(out)])
            self.assertEqual(code, 2)
            self.assertFalse(out.exists())

    def test_invalid_rating_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            messages, ratings = _write_fixture(folder)
            with open(ratings / "FIXTURE_A.csv", "a", encoding="utf-8", newline="") as stream:
                csv.writer(stream).writerow(["FX-01", "FX1", 1, "FIXTURE_A", 12, 3, 5, "neutral", "ANSWER", ""])
            with self.assertRaises(ValueError):
                evaluate.main(["--split", "dev", "--messages", str(messages), "--ratings-dir", str(ratings),
                               "--out", str(Path(folder) / "results")])

    def test_ablation_config_is_restored(self):
        from engine import config
        before = config.NEGATION_FACTOR
        with evaluate.patched_config(NEGATION_FACTOR=1.0):
            self.assertEqual(config.NEGATION_FACTOR, 1.0)
        self.assertEqual(config.NEGATION_FACTOR, before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
