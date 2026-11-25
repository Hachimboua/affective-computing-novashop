"""Compute reference feature statistics from the bundled audio fixtures."""
import argparse
import json
from pathlib import Path
import statistics

from engine.voice.features import extract_wav_features


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AUDIO_DIR = PROJECT_ROOT / "assets" / "audio"
DEFAULT_OUTPUT = PROJECT_ROOT / "engine" / "voice" / "reference_stats.json"
REFERENCE_FEATURES = ("energy_db", "f0_variability", "speaking_rate")


def compute_reference(audio_dir=DEFAULT_AUDIO_DIR, output_path=DEFAULT_OUTPUT):
    """Write population means and deviations for the reference WAV files."""
    audio_dir = Path(audio_dir)
    output_path = Path(output_path)
    audio_paths = sorted(audio_dir.glob("*.wav"))
    if not audio_paths:
        raise ValueError("No WAV reference files were found in %s." % audio_dir)

    extracted = [
        (path.name, extract_wav_features(path)) for path in audio_paths
    ]
    statistics_by_feature = {}
    for feature in REFERENCE_FEATURES:
        values = [float(features[feature]) for _, features in extracted]
        statistics_by_feature[feature] = {
            "mean": statistics.mean(values),
            "std": statistics.pstdev(values),
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "sources": [name for name, _ in extracted],
        "statistics": statistics_by_feature,
        "note": (
            "Fixture-derived reference only; pitch-based activity is based on "
            "variability, not absolute F0, because both speaker fixtures are calm."
        ),
    }
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return len(audio_paths)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio-dir", type=Path, default=DEFAULT_AUDIO_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args(argv)
    count = compute_reference(arguments.audio_dir, arguments.output)
    print(
        "Wrote voice reference statistics from %d WAV fixtures to %s."
        % (count, arguments.output)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
