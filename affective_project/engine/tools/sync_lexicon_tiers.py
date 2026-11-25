"""Sync reviewed tier choices from the project review sheet into TSV lexicons."""
import argparse
import csv
import os
from pathlib import Path
import tempfile

from engine.config import TIER_VAD


LEXICON_DIR = Path(__file__).resolve().parents[1] / "perception" / "lexicons"
LEXICON_FILES = ("en.tsv", "pt.tsv", "phrases_en.tsv", "phrases_pt.tsv")
HEADER = ("term", "tier", "v_override", "a_override", "d_override")
REQUIRED_COLUMNS = {"Lexicon", "term", "suggested tier", "my tier"}


def sync_tiers(sheet_path, lexicon_dir=LEXICON_DIR):
    """Write my tier when present, otherwise suggested tier, into each TSV."""
    sheet_path = Path(sheet_path)
    lexicon_dir = Path(lexicon_dir)
    with sheet_path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not REQUIRED_COLUMNS.issubset(reader.fieldnames or ()):
            raise ValueError("The review sheet is missing required tier columns.")
        selected_tiers = {}
        for line_number, row in enumerate(reader, 2):
            filename = (row["Lexicon"] or "").strip()
            term = (row["term"] or "").strip().lower()
            if filename not in LEXICON_FILES or not term:
                raise ValueError(
                    "Review sheet row %d has an unknown lexicon or empty term."
                    % line_number
                )
            tier = (row["my tier"] or "").strip() or (
                (row["suggested tier"] or "").strip()
            )
            tier = tier.upper()
            if tier not in TIER_VAD:
                raise ValueError(
                    "Review sheet row %d has an unknown tier %r."
                    % (line_number, tier)
                )
            key = (filename, term)
            if key in selected_tiers:
                raise ValueError(
                    "Review sheet has a duplicate entry for %s:%s."
                    % key
                )
            selected_tiers[key] = tier

    updated_contents = {}
    seen_entries = set()
    for filename in LEXICON_FILES:
        path = lexicon_dir / filename
        lines = path.read_text(encoding="utf-8").splitlines()
        output_lines = []
        found_header = False
        for line_number, line in enumerate(lines, 1):
            if not line or line.startswith("#"):
                output_lines.append(line)
                continue
            fields = line.split("\t")
            if tuple(fields) == HEADER:
                if found_header:
                    raise ValueError("%s has a duplicate header." % path)
                found_header = True
                output_lines.append(line)
                continue
            if len(fields) != len(HEADER):
                raise ValueError(
                    "%s:%d must have %d tab-separated columns."
                    % (path, line_number, len(HEADER))
                )
            key = (filename, fields[0].strip().lower())
            if key not in selected_tiers:
                raise ValueError(
                    "Review sheet has no tier choice for %s:%s."
                    % key
                )
            fields[1] = selected_tiers[key]
            output_lines.append("\t".join(fields))
            seen_entries.add(key)
        if not found_header:
            raise ValueError("%s is missing the tiered lexicon header." % path)
        updated_contents[path] = "\n".join(output_lines) + "\n"

    extra_entries = set(selected_tiers) - seen_entries
    if extra_entries:
        filename, term = sorted(extra_entries)[0]
        raise ValueError(
            "Review sheet has no matching TSV entry for %s:%s."
            % (filename, term)
        )

    temporary_paths = []
    try:
        for path, content in updated_contents.items():
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                dir=str(lexicon_dir),
                prefix=path.name + ".",
                suffix=".tmp",
                delete=False,
            ) as stream:
                stream.write(content)
                temporary_paths.append((Path(stream.name), path))
        for temporary_path, target_path in temporary_paths:
            os.replace(str(temporary_path), str(target_path))
    finally:
        for temporary_path, _ in temporary_paths:
            if temporary_path.exists():
                temporary_path.unlink()
    return len(seen_entries)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "review_sheet",
        type=Path,
        help="Review CSV containing suggested tier and my tier values",
    )
    arguments = parser.parse_args()
    count = sync_tiers(arguments.review_sheet)
    print("Synced tiers for %d lexicon entries." % count)


if __name__ == "__main__":
    main()
