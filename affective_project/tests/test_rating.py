"""Focused tests for the human-rating workflow."""
import csv
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from engine.evaluation.rate import (
    LABELS,
    load_completed_ids,
    load_messages,
    parse_scale_value,
    rate_messages,
    sanitize_rater_id,
)


class RatingInputTests(unittest.TestCase):
    def test_rating_labels_match_kit_vocabulary(self):
        self.assertEqual(
            LABELS,
            ("neutral", "calm", "joy", "anger", "frustration", "fear", "sadness"),
        )

    def test_scale_accepts_only_integer_values_from_one_to_nine(self):
        self.assertEqual(parse_scale_value("5", "valence"), 5)
        for value in ("0", "10", "2.5", "", "word"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_scale_value(value, "valence")

    def test_rater_id_is_safe_for_a_filename(self):
        self.assertEqual(sanitize_rater_id("Rater_01"), "Rater_01")
        for value in ("../person", "name with spaces", ""):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    sanitize_rater_id(value)

    def test_rating_file_can_resume_from_completed_message_ids(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "rater.csv"
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=("msg_id", "valence"))
                writer.writeheader()
                writer.writerow({"msg_id": "M1-01", "valence": 6})
            self.assertEqual(load_completed_ids(path), {"M1-01"})

    def test_rating_cli_resumes_and_shows_earlier_turns(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            dataset = root / "messages.csv"
            with dataset.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(
                    stream,
                    fieldnames=(
                        "msg_id",
                        "conversation_id",
                        "turn",
                        "split",
                        "text",
                        "source",
                        "case_type",
                    ),
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "msg_id": "C1-01",
                        "conversation_id": "C1",
                        "turn": 1,
                        "split": "dev",
                        "text": "My delivery is late.",
                        "source": "ai_draft",
                        "case_type": "delay",
                    }
                )
                writer.writerow(
                    {
                        "msg_id": "C1-02",
                        "conversation_id": "C1",
                        "turn": 2,
                        "split": "dev",
                        "text": "I still need help.",
                        "source": "ai_draft",
                        "case_type": "delay",
                    }
                )
            ratings_dir = root / "ratings"
            ratings_dir.mkdir()
            existing = ratings_dir / "R01.csv"
            with existing.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(
                    stream,
                    fieldnames=(
                        "msg_id",
                        "conversation_id",
                        "turn",
                        "rater_id",
                        "valence",
                        "arousal",
                        "dominance",
                        "label",
                        "action",
                        "comment",
                    ),
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "msg_id": "C1-01",
                        "conversation_id": "C1",
                        "turn": 1,
                        "rater_id": "R01",
                        "valence": 3,
                        "arousal": 5,
                        "dominance": 4,
                        "label": "frustration",
                        "action": "ANSWER_EMPATHIC",
                        "comment": "",
                    }
                )

            answers = ["5", "6", "4", "neutral", "ANSWER", ""]
            output = StringIO()
            with patch("builtins.input", side_effect=answers), redirect_stdout(output):
                rate_messages("R01", dataset=dataset, ratings_dir=ratings_dir)

            with existing.open("r", encoding="utf-8", newline="") as stream:
                rated = list(csv.DictReader(stream))
            self.assertEqual([row["msg_id"] for row in rated], ["C1-01", "C1-02"])
            self.assertIn("My delivery is late.", output.getvalue())

    def test_dataset_has_conversation_consistent_splits_and_expected_sources(self):
        messages = load_messages()
        splits = {}
        counts = {}
        for message in messages:
            conversation_id = message["conversation_id"]
            splits.setdefault(conversation_id, set()).add(message["split"])
            counts[conversation_id] = counts.get(conversation_id, 0) + 1
        self.assertTrue(all(len(values) == 1 for values in splits.values()))
        self.assertEqual(sum(m["source"] == "scenario" for m in messages), 28)
        self.assertEqual(sum(m["source"] == "ai_draft" for m in messages), 60)
        self.assertTrue(
            all(m["split"] == "dev" for m in messages if m["source"] == "scenario")
        )
        self.assertEqual(
            {m["split"] for m in messages if m["source"] == "ai_draft"},
            {"dev", "test"},
        )
        split_counts = {"dev": 0, "test": 0}
        for values in splits.values():
            split_counts[next(iter(values))] += 1
        self.assertEqual(split_counts, {"dev": 18, "test": 10})
        self.assertTrue(
            all(
                count == 3
                for conversation_id, count in counts.items()
                if conversation_id.startswith("AI-")
            )
        )

    def test_spreadsheet_template_has_all_messages_and_blank_rating_cells(self):
        root = Path(__file__).resolve().parents[1]
        template = root / "engine" / "evaluation" / "sam_ratings_template.csv"
        with template.open("r", encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 88)
        self.assertTrue(all(row["text"] for row in rows))
        dataset_texts = {
            row["msg_id"]: row["text"] for row in load_messages()
        }
        self.assertEqual(
            {row["msg_id"]: row["text"] for row in rows},
            dataset_texts,
        )
        for field in ("valence", "arousal", "dominance", "label", "action", "comment"):
            with self.subTest(field=field):
                self.assertTrue(all(row[field] == "" for row in rows))


if __name__ == "__main__":
    unittest.main(verbosity=2)
