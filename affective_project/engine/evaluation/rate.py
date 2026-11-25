"""Collect human SAM ratings without loading or displaying engine predictions."""
import argparse
import csv
import re
from pathlib import Path


HERE = Path(__file__).resolve().parent
DATASET = HERE / "data" / "messages.csv"
RATINGS_DIR = HERE / "ratings"
FIELDS = (
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
)
LABELS = (
    "neutral",
    "calm",
    "joy",
    "anger",
    "frustration",
    "fear",
    "sadness",
)
ACTIONS = (
    "ANSWER",
    "ANSWER_EMPATHIC",
    "ASK_CLARIFICATION",
    "OFFER_HUMAN",
    "ESCALATE",
    "CLOSE_POSITIVE",
)
MESSAGE_FIELDS = (
    "msg_id",
    "conversation_id",
    "turn",
    "split",
    "text",
    "source",
    "case_type",
)


def sanitize_rater_id(value):
    """Keep rater IDs usable as filenames and avoid path traversal."""
    value = value.strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", value):
        raise ValueError("Rater ID must use 1-40 letters, digits, '_' or '-'.")
    return value


def parse_scale_value(value, dimension):
    """Validate one integer response on a 9-point SAM scale."""
    try:
        rating = int(value.strip())
    except (AttributeError, ValueError):
        raise ValueError("%s must be a whole number from 1 to 9." % dimension)
    if str(rating) != value.strip() or not 1 <= rating <= 9:
        raise ValueError("%s must be a whole number from 1 to 9." % dimension)
    return rating


def load_messages(path=DATASET):
    """Load messages and validate IDs, turns, splits, and required fields."""
    messages = []
    seen = set()
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != list(MESSAGE_FIELDS):
            raise ValueError("Message CSV must use the documented column order.")
        for row in reader:
            if not all(row.get(field) for field in MESSAGE_FIELDS):
                raise ValueError("Every message row must have all required fields.")
            if row["msg_id"] in seen:
                raise ValueError("Duplicate msg_id: %s" % row["msg_id"])
            if row["split"] not in ("dev", "test"):
                raise ValueError("split must be 'dev' or 'test'.")
            try:
                row["turn"] = int(row["turn"])
            except ValueError:
                raise ValueError("turn must be a positive integer.")
            if row["turn"] < 1:
                raise ValueError("turn must be a positive integer.")
            seen.add(row["msg_id"])
            messages.append(row)
    return messages


def load_completed_ids(path):
    """Return message IDs already rated so an interrupted session can resume."""
    if not path.exists() or path.stat().st_size == 0:
        return set()
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or "msg_id" not in reader.fieldnames:
            raise ValueError("Existing rating file has no msg_id column.")
        return {row["msg_id"] for row in reader if row.get("msg_id")}


def _prompt_scale(dimension):
    while True:
        raw = input("%s (1-9): " % dimension)
        try:
            return parse_scale_value(raw, dimension)
        except ValueError as exc:
            print(exc)


def _prompt_choice(prompt, choices):
    for index, choice in enumerate(choices, 1):
        print("%d. %s" % (index, choice))
    while True:
        answer = input(prompt + " (number or name): ").strip()
        if answer.isdigit() and 1 <= int(answer) <= len(choices):
            return choices[int(answer) - 1]
        for choice in choices:
            if answer.lower() == choice.lower():
                return choice
        print("Choose one of the listed options.")


def rate_messages(rater_id, dataset=DATASET, ratings_dir=RATINGS_DIR):
    """Rate each message with conversation context and append answers as given."""
    rater_id = sanitize_rater_id(rater_id)
    messages = load_messages(dataset)
    ratings_dir.mkdir(parents=True, exist_ok=True)
    output = ratings_dir / (rater_id + ".csv")
    completed = load_completed_ids(output)
    needs_header = not output.exists() or output.stat().st_size == 0
    earlier = {}

    with output.open("a", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        if needs_header:
            writer.writeheader()
            stream.flush()

        for message in messages:
            conversation_id = message["conversation_id"]
            history = earlier.setdefault(conversation_id, [])
            if message["msg_id"] in completed:
                history.append(message["text"])
                continue

            print("\nConversation %s, turn %d" % (conversation_id, message["turn"]))
            if history:
                print("Earlier turns:")
                for turn, text in enumerate(history, 1):
                    print("  %d. Customer: %s" % (turn, text))
            print("Current customer message: %s" % message["text"])
            print("Rate the emotion expressed in the text, not what you would feel.")

            valence = _prompt_scale("Valence / pleasure")
            arousal = _prompt_scale("Arousal / activity")
            dominance = _prompt_scale("Dominance / control")
            label = _prompt_choice("Best-fitting label", LABELS)
            action = _prompt_choice("Best customer-support action", ACTIONS)
            comment = input("Optional comment (press Enter to leave blank): ").strip()

            writer.writerow(
                {
                    "msg_id": message["msg_id"],
                    "conversation_id": conversation_id,
                    "turn": message["turn"],
                    "rater_id": rater_id,
                    "valence": valence,
                    "arousal": arousal,
                    "dominance": dominance,
                    "label": label,
                    "action": action,
                    "comment": comment,
                }
            )
            stream.flush()
            history.append(message["text"])

    print("Ratings saved to %s" % output)
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Rate customer messages using 9-point SAM scales."
    )
    parser.add_argument("--rater", required=True, help="Anonymous rater ID, not a name")
    args = parser.parse_args(argv)
    rate_messages(args.rater)


if __name__ == "__main__":
    main()
