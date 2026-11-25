"""Compare the engine with human SAM ratings.

Usage (from the affective_project folder):

    python -m engine.evaluation.evaluate --split dev
    python -m engine.evaluation.evaluate --split test
    python -m engine.evaluation.evaluate --voice-check

What it does
------------
1. Loads the rating files written by ``python -m engine.evaluation.rate``
   (one CSV per rater in ``engine/evaluation/ratings/``). Without any real
   rating file it stops with exit code 2: it never invents ratings.
2. Builds the gold standard per message: mean SAM rating converted to [-1, 1]
   for valence, activity and dominance; majority vote for label and action.
3. Replays every conversation of the chosen split in order, with a fresh
   engine per conversation, for several variants: the kit's starter engine,
   the full engine, and ablations that switch one component off.
4. Computes correlation, error, label and action metrics (with bootstrap
   confidence intervals), agreement between raters, confidence calibration,
   and the largest errors for the error analysis.
5. Writes JSON, CSV and Markdown files to ``engine/evaluation/results/``.

Tune only on the dev split. The test split gives the honest numbers.
"""
import argparse
import contextlib
import csv
import importlib.util
import io
import json
import os
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from engine import config  # noqa: E402
from engine.engine import Engine  # noqa: E402
from engine.evaluation import metrics  # noqa: E402
from engine.evaluation.rate import ACTIONS, LABELS  # noqa: E402

DEFAULT_MESSAGES = HERE / "data" / "messages.csv"
DEFAULT_RATINGS = HERE / "ratings"
DEFAULT_RESULTS = HERE / "results"
STARTER_PATH = HERE / "baselines" / "starter_engine.py"
DIMENSIONS = ("valence", "activity", "dominance")
RATING_COLUMNS = {"valence": "valence", "activity": "arousal", "dominance": "dominance"}

# Cost of each kind of action mistake (gold -> predicted). Missing a needed
# escalation is the most harmful error; an unnecessary handoff is mild.
ACTION_COST = {
    ("ESCALATE", "OFFER_HUMAN"): 1.0,
    ("OFFER_HUMAN", "ESCALATE"): 1.0,
}
MISSED_ESCALATION_COST = 3.0
MISSED_HUMAN_COST = 2.0
DEFAULT_ERROR_COST = 1.0

SUGGESTED_CATEGORY_FLAGS = (
    ("possible_sarcasm", "sarcasm"),
    ("negation", "negation"),
    ("unsupported_language", "other language"),
    ("mixed_language", "other language"),
    ("short_message", "short or ambiguous"),
    ("mixed_emotion", "mixed emotion"),
    ("no_affect_words", "missing lexicon term or neutral wording"),
)


# --------------------------------------------------------------------------
# Loading data
# --------------------------------------------------------------------------
def load_messages(path):
    with open(path, encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _read_csv(path):
    """Read a CSV written by the rating tool or saved from a spreadsheet.

    Spreadsheets may add a UTF-8 byte-order mark and, on some Windows language
    settings, use ';' instead of ',' between columns. Both are accepted.
    """
    with open(path, encoding="utf-8-sig", newline="") as stream:
        text = stream.read()
    header = text.split("\n", 1)[0]
    counts = {delimiter: header.count(delimiter) for delimiter in (",", ";", "\t")}
    delimiter = max(counts, key=counts.get) if max(counts.values()) else ","
    return list(csv.DictReader(io.StringIO(text, newline=""), delimiter=delimiter))


def load_ratings(ratings_dir):
    """Return a list of validated rating rows from every rater CSV.

    Rows where all three SAM values are empty are treated as "not rated yet"
    and skipped (a volunteer may stop half-way). Partly filled rows, values
    outside 1..9, or an unknown label/action are rejected with a clear error,
    because silently skipping them would bias the results. When a spreadsheet
    row has no rater_id, the file name (e.g. R2.csv -> R2) is used.
    """
    ratings_dir = Path(ratings_dir)
    if not ratings_dir.is_dir():
        return []
    rows = []
    for path in sorted(ratings_dir.glob("*.csv")):
        for line_number, row in enumerate(_read_csv(path), start=2):
            values = [(row.get(column) or "").strip() for column in RATING_COLUMNS.values()]
            if not any(values):
                continue
            if not all(values):
                raise ValueError("%s line %d: fill valence, arousal and dominance (or leave all three empty)" % (path.name, line_number))
            for column in RATING_COLUMNS.values():
                value = int(float(row[column]))
                if not 1 <= value <= 9:
                    raise ValueError("%s line %d: %s=%s is outside 1..9" % (path.name, line_number, column, value))
                row[column] = value
            row["label"] = (row.get("label") or "").strip().lower()
            row["action"] = (row.get("action") or "").strip().upper()
            if row["label"] not in LABELS:
                raise ValueError("%s line %d: unknown label %r (use one of %s)" % (path.name, line_number, row["label"], ", ".join(LABELS)))
            if row["action"] not in ACTIONS:
                raise ValueError("%s line %d: unknown action %r (use one of %s)" % (path.name, line_number, row["action"], ", ".join(ACTIONS)))
            row["rater_id"] = (row.get("rater_id") or "").strip() or path.stem
            rows.append(row)
    return rows


def majority(values):
    """Most frequent value, or None when the top two are tied."""
    counts = Counter(values).most_common()
    if not counts:
        return None
    if len(counts) > 1 and counts[0][1] == counts[1][1]:
        return None
    return counts[0][0]


def build_gold(rating_rows):
    """Average the raters per message (dimensions) and take majority votes."""
    by_message = defaultdict(list)
    for row in rating_rows:
        by_message[row["msg_id"]].append(row)
    gold = {}
    for msg_id, rows in by_message.items():
        item = {"raters": len(rows)}
        for dimension, column in RATING_COLUMNS.items():
            item[dimension] = sum(metrics.sam_to_unit(row[column]) for row in rows) / float(len(rows))
        item["label"] = majority([row["label"] for row in rows])
        item["action"] = majority([row["action"] for row in rows])
        gold[msg_id] = item
    return gold


# --------------------------------------------------------------------------
# Engine variants
# --------------------------------------------------------------------------
def load_starter_engine():
    """Load the kit's starter engine from its file (the baseline)."""
    spec = importlib.util.spec_from_file_location("starter_engine_baseline", str(STARTER_PATH))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Engine()


@contextlib.contextmanager
def patched_config(**values):
    """Temporarily change config values (used for ablations), then restore."""
    old = {name: getattr(config, name) for name in values}
    try:
        for name, value in values.items():
            setattr(config, name, value)
        yield
    finally:
        for name, value in old.items():
            setattr(config, name, value)


def _no_smoothing_engine():
    """Full engine whose state follows each message without averaging."""
    engine = Engine()
    original_reset = engine.reset

    def reset():
        original_reset()
        tracker = engine.state_tracker

        def smooth(estimate):
            tracker.state = {
                "valence": float(estimate.valence),
                "activity": float(estimate.activity),
                "dominance": float(estimate.dominance),
            }

        tracker._smooth = smooth

    engine.reset = reset
    engine.reset()
    return engine


VARIANTS = (
    ("starter", "kit starter engine (baseline)", load_starter_engine, {}),
    ("full", "full engine", Engine, {}),
    ("no_negation", "full engine without negation", Engine, {"NEGATION_FACTOR": 1.0, "NEGATION_ACTIVITY_FACTOR": 1.0}),
    ("no_sarcasm", "full engine without sarcasm detection", Engine, {"SARCASM_THRESHOLD": 1.01}),
    ("no_smoothing", "full engine without state smoothing", _no_smoothing_engine, {}),
)


def run_variant(factory, overrides, conversations):
    """Replay each conversation in order with a fresh engine; return outputs."""
    outputs = {}
    latencies = []
    with patched_config(**overrides):
        for conversation in conversations:
            engine = factory()
            engine.reset()
            for message in conversation:
                started = time.perf_counter()
                result = engine.process(message["text"])
                latencies.append((time.perf_counter() - started) * 1000.0)
                outputs[message["msg_id"]] = {
                    "valence": float(result.get("valence", 0.0)),
                    "activity": float(result.get("activity", result.get("arousal", 0.0))),
                    "dominance": result.get("dominance"),
                    "confidence": float(result.get("confidence", 0.0)),
                    "label": str(result.get("label", "")),
                    "action": str(result.get("action", "")),
                    "flags": list(result.get("flags", [])),
                }
    return outputs, latencies


def conversations_for(messages, split):
    selected = [m for m in messages if split == "all" or m["split"] == split]
    grouped = defaultdict(list)
    for message in selected:
        grouped[message["conversation_id"]].append(message)
    return [sorted(items, key=lambda m: int(m["turn"])) for _, items in sorted(grouped.items())]


# --------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------
def action_cost(gold, predicted):
    if gold == predicted:
        return 0.0
    if (gold, predicted) in ACTION_COST:
        return ACTION_COST[(gold, predicted)]
    if gold == "ESCALATE":
        return MISSED_ESCALATION_COST
    if gold == "OFFER_HUMAN":
        return MISSED_HUMAN_COST
    return DEFAULT_ERROR_COST


def _round(value, digits=3):
    if value is None:
        return None
    if isinstance(value, tuple):
        return [round(v, digits) for v in value]
    return round(value, digits)


def score_variant(gold, outputs, bootstrap, seed):
    ids = [msg_id for msg_id in sorted(gold) if msg_id in outputs]
    result = {"messages": len(ids), "dimensions": {}}
    for dimension in DIMENSIONS:
        pairs = [(gold[i][dimension], outputs[i][dimension]) for i in ids if outputs[i][dimension] is not None]
        g = [p[0] for p in pairs]
        p = [p[1] for p in pairs]
        result["dimensions"][dimension] = {
            "n": len(pairs),
            "pearson": _round(metrics.pearson(g, p)),
            "pearson_ci": _round(metrics.bootstrap_ci(metrics.pearson, g, p, bootstrap, seed)),
            "spearman": _round(metrics.spearman(g, p)),
            "mae": _round(metrics.mae(g, p)),
            "mae_ci": _round(metrics.bootstrap_ci(metrics.mae, g, p, bootstrap, seed)),
            "rmse": _round(metrics.rmse(g, p)),
            "sign_accuracy": _round(metrics.sign_accuracy(g, p)),
        }
    for field, classes in (("label", LABELS), ("action", ACTIONS)):
        usable = [i for i in ids if gold[i][field] is not None]
        g = [gold[i][field] for i in usable]
        p = [outputs[i][field] for i in usable]
        names, matrix = metrics.confusion_matrix(g, p, list(classes))
        result[field] = {
            "n": len(usable),
            "ties_excluded": len(ids) - len(usable),
            "accuracy": _round(metrics.accuracy(g, p)),
            "macro_f1": _round(metrics.macro_f1(g, p, sorted(set(g) | set(p)))),
            "per_class": {k: {kk: _round(vv) for kk, vv in v.items()} for k, v in metrics.per_class_prf(g, p, sorted(set(g) | set(p))).items()},
            "confusion": {"classes": names, "matrix": matrix},
        }
        if field == "action":
            costs = [action_cost(a, b) for a, b in zip(g, p)]
            result[field]["mean_cost"] = _round(sum(costs) / len(costs)) if costs else None
    abs_errors = [abs(gold[i]["valence"] - outputs[i]["valence"]) for i in ids]
    confidences = [outputs[i]["confidence"] for i in ids]
    result["calibration"] = {
        "bins": [{**row, "mean_abs_error": _round(row["mean_abs_error"])} for row in metrics.calibration_bins(confidences, abs_errors)],
        "spearman_confidence_vs_error": _round(metrics.spearman(confidences, abs_errors)),
    }
    return result


def rater_agreement(rating_rows):
    """Agreement between raters; needs at least two raters."""
    raters = sorted({row["rater_id"] for row in rating_rows})
    if len(raters) < 2:
        return {"raters": len(raters), "note": "agreement needs at least two raters"}
    agreement = {"raters": len(raters), "dimensions": {}}
    by_message = defaultdict(dict)
    for row in rating_rows:
        by_message[row["msg_id"]][row["rater_id"]] = row
    for dimension, column in RATING_COLUMNS.items():
        units = [[float(r[column]) for r in rows.values()] for rows in by_message.values()]
        series = defaultdict(dict)
        for msg_id, rows in by_message.items():
            for rater, r in rows.items():
                series[rater][msg_id] = float(r[column])
        agreement["dimensions"][dimension] = {
            "krippendorff_alpha_interval": _round(metrics.krippendorff_alpha_interval(units)),
            "mean_pairwise_pearson": _round(metrics.mean_pairwise_pearson(series)),
        }
    complete = [rows for rows in by_message.values() if len(rows) == len(raters)]
    for field, classes in (("label", LABELS), ("action", ACTIONS)):
        table = [[sum(1 for r in rows.values() if r[field] == name) for name in classes] for rows in complete]
        agreement[field + "_fleiss_kappa"] = _round(metrics.fleiss_kappa(table))
    agreement["messages_rated_by_all"] = len(complete)
    return agreement


def error_rows(gold, outputs, messages, limit=15):
    """The largest valence+activity errors, with a suggested category."""
    by_id = {m["msg_id"]: m for m in messages}
    rows = []
    for msg_id in gold:
        if msg_id not in outputs:
            continue
        out = outputs[msg_id]
        error = abs(gold[msg_id]["valence"] - out["valence"]) + abs(gold[msg_id]["activity"] - out["activity"])
        suggested = "other"
        for flag, category in SUGGESTED_CATEGORY_FLAGS:
            if flag in out["flags"]:
                suggested = category
                break
        rows.append({
            "msg_id": msg_id,
            "case_type": by_id[msg_id]["case_type"],
            "text": by_id[msg_id]["text"],
            "gold_v": round(gold[msg_id]["valence"], 3),
            "pred_v": round(out["valence"], 3),
            "gold_a": round(gold[msg_id]["activity"], 3),
            "pred_a": round(out["activity"], 3),
            "gold_label": gold[msg_id]["label"],
            "pred_label": out["label"],
            "gold_action": gold[msg_id]["action"],
            "pred_action": out["action"],
            "confidence": round(out["confidence"], 3),
            "combined_error": round(error, 3),
            "suggested_category": suggested,
            "my_category": "",
        })
    rows.sort(key=lambda r: r["combined_error"], reverse=True)
    return rows[:limit]


# --------------------------------------------------------------------------
# Voice check (uses only the kit audio files, no ratings needed)
# --------------------------------------------------------------------------
def voice_check(project=PROJECT):
    """Check the voice channel against the expectations in assets/audio/README.txt."""
    from engine.voice.features import numpy_available
    if not numpy_available():
        return {"available": False, "note": "numpy is not installed; the voice channel is off"}
    from engine.voice.voice_estimator import estimate_voice
    audio = Path(project) / "assets" / "audio"
    names = ("calm_clean", "agitated_clean", "calm_noisy", "agitated_noisy", "speaker_low", "speaker_high")
    estimates = {}
    for name in names:
        estimate = estimate_voice(str(audio / (name + ".wav")))
        estimates[name] = {"activity": round(float(estimate.activity), 3), "confidence": round(float(estimate.confidence), 3)}
    checks = {
        "agitated_clean more activated than calm_clean": estimates["agitated_clean"]["activity"] > estimates["calm_clean"]["activity"],
        "speaker_low and speaker_high both calm (activity < 0.1)": estimates["speaker_low"]["activity"] < 0.1 and estimates["speaker_high"]["activity"] < 0.1,
        "calm_noisy confidence lower than calm_clean": estimates["calm_noisy"]["confidence"] < estimates["calm_clean"]["confidence"],
        "agitated_noisy confidence lower than agitated_clean": estimates["agitated_noisy"]["confidence"] < estimates["agitated_clean"]["confidence"],
    }
    return {"available": True, "estimates": estimates, "checks": checks}


# --------------------------------------------------------------------------
# Reports
# --------------------------------------------------------------------------
def _fmt(value):
    if value is None:
        return "n/a"
    if isinstance(value, list):
        return "[%s, %s]" % (_fmt(value[0]), _fmt(value[1]))
    return "%.3f" % value if isinstance(value, float) else str(value)


def write_summary(path, split, report):
    lines = ["# Evaluation summary: %s split" % split, ""]
    lines.append("Raters: %s. Messages with ratings in this split: %s." % (report["agreement"]["raters"], report["variants"]["full"]["messages"]))
    lines += ["", "## Engine vs human ratings", "",
              "| Variant | V Pearson [95% CI] | V MAE | A Pearson | A MAE | D Pearson | Label acc | Label macro-F1 | Action acc | Action macro-F1 | Action cost |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, description, _, _ in VARIANTS:
        v = report["variants"][name]
        d = v["dimensions"]
        lines.append("| %s | %s %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            description, _fmt(d["valence"]["pearson"]), _fmt(d["valence"]["pearson_ci"]), _fmt(d["valence"]["mae"]),
            _fmt(d["activity"]["pearson"]), _fmt(d["activity"]["mae"]), _fmt(d["dominance"]["pearson"]),
            _fmt(v["label"]["accuracy"]), _fmt(v["label"]["macro_f1"]), _fmt(v["action"]["accuracy"]),
            _fmt(v["action"]["macro_f1"]), _fmt(v["action"]["mean_cost"])))
    lines += ["", "## Agreement between raters", ""]
    agreement = report["agreement"]
    if "dimensions" in agreement:
        for dimension, values in agreement["dimensions"].items():
            lines.append("- %s: Krippendorff alpha %s, mean pairwise Pearson %s" % (dimension, _fmt(values["krippendorff_alpha_interval"]), _fmt(values["mean_pairwise_pearson"])))
        lines.append("- label Fleiss kappa %s; action Fleiss kappa %s (messages rated by all: %s)" % (_fmt(agreement["label_fleiss_kappa"]), _fmt(agreement["action_fleiss_kappa"]), agreement["messages_rated_by_all"]))
    else:
        lines.append("- %s" % agreement["note"])
    lines += ["", "## Confidence calibration (full engine, valence error)", "", "| Confidence | n | Mean abs error |", "|---|---|---|"]
    for row in report["variants"]["full"]["calibration"]["bins"]:
        lines.append("| %s | %s | %s |" % (row["bin"], row["count"], _fmt(row["mean_abs_error"])))
    lines.append("")
    lines.append("Spearman(confidence, error): %s (negative is good: more confidence, less error)." % _fmt(report["variants"]["full"]["calibration"]["spearman_confidence_vs_error"]))
    lines += ["", "Latency (full engine): median %s ms, max %s ms." % (_fmt(report["latency_ms"]["median"]), _fmt(report["latency_ms"]["max"])), "",
              "Largest errors: see `%s_errors.csv` (fill the `my_category` column yourself)." % split, ""]
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def evaluate(split, messages_path, ratings_dir, out_dir, bootstrap, seed):
    messages = load_messages(messages_path)
    rating_rows = load_ratings(ratings_dir)
    split_ids = {m["msg_id"] for m in messages if split == "all" or m["split"] == split}
    rating_rows = [row for row in rating_rows if row["msg_id"] in split_ids]
    if not rating_rows:
        return None
    gold = build_gold(rating_rows)
    conversations = conversations_for(messages, split)
    report = {"split": split, "agreement": rater_agreement(rating_rows), "variants": {}}
    full_outputs = None
    for name, _, factory, overrides in VARIANTS:
        outputs, latencies = run_variant(factory, overrides, conversations)
        report["variants"][name] = score_variant(gold, outputs, bootstrap, seed)
        if name == "full":
            full_outputs = outputs
            ordered = sorted(latencies)
            report["latency_ms"] = {"median": round(ordered[len(ordered) // 2], 3), "max": round(ordered[-1], 3)}
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / ("%s_metrics.json" % split)).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_summary(out_dir / ("%s_summary.md" % split), split, report)
    with open(out_dir / ("%s_predictions.csv" % split), "w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["msg_id", "gold_v", "gold_a", "gold_d", "gold_label", "gold_action", "pred_v", "pred_a", "pred_d", "pred_label", "pred_action", "confidence", "flags"])
        for msg_id in sorted(gold):
            if msg_id not in full_outputs:
                continue
            g, p = gold[msg_id], full_outputs[msg_id]
            writer.writerow([msg_id, round(g["valence"], 3), round(g["activity"], 3), round(g["dominance"], 3), g["label"], g["action"],
                             round(p["valence"], 3), round(p["activity"], 3), None if p["dominance"] is None else round(p["dominance"], 3),
                             p["label"], p["action"], round(p["confidence"], 3), " ".join(p["flags"])])
    errors = error_rows(gold, full_outputs, messages)
    with open(out_dir / ("%s_errors.csv" % split), "w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(errors[0].keys()) if errors else ["msg_id"])
        writer.writeheader()
        writer.writerows(errors)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--split", choices=("dev", "test", "all"), default="dev")
    parser.add_argument("--messages", default=str(DEFAULT_MESSAGES))
    parser.add_argument("--ratings-dir", default=str(DEFAULT_RATINGS))
    parser.add_argument("--out", default=str(DEFAULT_RESULTS))
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--voice-check", action="store_true", help="only check the voice channel on the kit audio files")
    args = parser.parse_args(argv)

    if args.voice_check:
        result = voice_check()
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "voice_check.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result, indent=2))
        return 0 if result.get("available") and all(result["checks"].values()) else 1

    report = evaluate(args.split, args.messages, args.ratings_dir, args.out, args.bootstrap, args.seed)
    if report is None:
        print("No SAM ratings found for the %s split in %s." % (args.split, args.ratings_dir))
        print("Collect them first:  python -m engine.evaluation.rate --rater R1")
        print("Nothing was evaluated and no numbers were written.")
        return 2
    print("Wrote results for the %s split to %s" % (args.split, args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
