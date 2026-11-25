"""Build the delivery zip: GroupXX_AffectiveComputing.zip.

Usage (from the AC solo folder, after the report and video exist):

    py -3.12 affective_project_notes/tools/package.py ^
        --group Group07 ^
        --report path/to/report.pdf ^
        --video path/to/video_demo.mp4 ^
        --demo-log affective_project/logs/session_20261201_101500.txt ^
        --kit-zip "path/to/Student_Kit_to_share_with_students.zip" ^
        --ratings include

The zip contains exactly what the brief asks for (section 5):
    report.pdf
    video_demo.mp4
    code/            the project folder with our engine, its README, the
                     requirements file and the log of the demo session

Before writing the zip the script:
  1. refuses to run if the report or video is missing or has the wrong type;
  2. copies affective_project/ to a staging folder without __pycache__ and
     without session logs (only the demo log you name is kept);
  3. checks every protected kit file against the original kit zip;
  4. runs the contract test, all tests and all scenarios inside the staged
     code/ folder, exactly as the teacher would;
  5. prints a manifest with sizes.
Nothing in the project is modified.
"""
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
WORKSPACE_ROOT = TOOLS.parents[1]
PROJECT_ROOT = WORKSPACE_ROOT / "affective_project"
sys.path.insert(0, str(TOOLS))
import verify_kit  # noqa: E402

ERROR_LINE = re.compile(r"(?m)^\s*(?:PROBLEMS|ERROR)\s*:")
IGNORED = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".pytest_cache", ".venv", "venv", ".git")


def _run(command, cwd):
    return subprocess.run(command, cwd=str(cwd), stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, universal_newlines=True, timeout=600)


def _human(size):
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return "%.1f %s" % (size, unit) if unit != "B" else "%d B" % size
        size /= 1024.0
    return str(size)


def stage_code(destination, demo_log, include_ratings):
    """Copy the project to destination/code and keep only the demo log."""
    code = destination / "code"
    shutil.copytree(str(PROJECT_ROOT), str(code), ignore=IGNORED)
    for log in (code / "logs").glob("session_*.txt"):
        log.unlink()
    shutil.copy2(str(demo_log), str(code / "logs" / Path(demo_log).name))
    ratings = code / "engine" / "evaluation" / "ratings"
    if not include_ratings and ratings.exists():
        shutil.rmtree(str(ratings))
    return code


def check_code(code):
    """Run the teacher-style checks inside the staged code folder."""
    failures = []
    contract = _run([sys.executable, "tests/test_contract.py"], code)
    if contract.returncode:
        failures.append("contract test failed:\n" + contract.stdout[-2000:])
    tests = _run([sys.executable, "-m", "unittest", "discover", "tests"], code)
    if tests.returncode:
        failures.append("unit tests failed:\n" + tests.stdout[-3000:])
    before = set((code / "logs").glob("session_*.txt"))
    for scenario in sorted((code / "scenarios").rglob("*.json")):
        result = _run([sys.executable, "run_scenario.py", str(scenario.relative_to(code))], code)
        if result.returncode or ERROR_LINE.search(result.stdout):
            failures.append("scenario %s failed:\n%s" % (scenario.name, result.stdout[-1500:]))
    for log in set((code / "logs").glob("session_*.txt")) - before:
        text = log.read_text(encoding="utf-8", errors="replace")
        if ERROR_LINE.search(text):
            failures.append("problems in scenario log %s" % log.name)
        log.unlink()
    for cache in code.rglob("__pycache__"):
        shutil.rmtree(str(cache), ignore_errors=True)
    match = re.search(r"Ran (\d+) tests", tests.stdout)
    return failures, int(match.group(1)) if match else 0


def build_zip(zip_path, staging):
    with zipfile.ZipFile(str(zip_path), "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(staging.rglob("*")):
            if path.is_file():
                archive.write(str(path), path.relative_to(staging).as_posix())


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build GroupXX_AffectiveComputing.zip")
    parser.add_argument("--group", required=True, help="group id, e.g. Group07")
    parser.add_argument("--report", required=True, help="path to report.pdf")
    parser.add_argument("--video", required=True, help="path to video_demo.mp4")
    parser.add_argument("--demo-log", required=True, help="session log recorded during the video")
    parser.add_argument("--kit-zip", required=True, help="original kit zip, for the byte-for-byte check")
    parser.add_argument("--ratings", choices=("include", "exclude"), required=True,
                        help="include the anonymous rating files in code/ (only if the consent form allows it)")
    parser.add_argument("--out", default=str(WORKSPACE_ROOT / "dist"), help="output folder")
    parser.add_argument("--allow-placeholder-group", action="store_true")
    args = parser.parse_args(argv)

    problems = []
    if args.group == "GroupXX" and not args.allow_placeholder_group:
        problems.append("replace GroupXX with your real group id (or pass --allow-placeholder-group for a test run)")
    report, video, demo_log = Path(args.report), Path(args.video), Path(args.demo_log)
    if not report.is_file() or report.suffix.lower() != ".pdf":
        problems.append("report not found or not a .pdf: %s" % report)
    if not video.is_file() or video.suffix.lower() != ".mp4":
        problems.append("video not found or not an .mp4: %s" % video)
    if not demo_log.is_file() or not demo_log.name.startswith("session_"):
        problems.append("demo log not found or not a session_*.txt file: %s" % demo_log)
    if not Path(args.kit_zip).is_file():
        problems.append("original kit zip not found: %s" % args.kit_zip)
    if problems:
        print("Packaging refused:")
        for problem in problems:
            print("  - " + problem)
        return 1

    name = "%s_AffectiveComputing.zip" % args.group
    with tempfile.TemporaryDirectory(prefix="novashop-package-") as temp:
        staging = Path(temp) / "package"
        staging.mkdir()
        shutil.copy2(str(report), str(staging / "report.pdf"))
        shutil.copy2(str(video), str(staging / "video_demo.mp4"))
        code = stage_code(staging, demo_log, args.ratings == "include")

        mismatches, checked = verify_kit.verify(args.kit_zip, project_root=code)
        if mismatches:
            print("Packaging refused: %d protected kit files differ from the original:" % len(mismatches))
            for relative, reason in mismatches:
                print("  - %s: %s" % (relative, reason))
            return 1
        print("Protected kit files: %d checked, 0 mismatches." % checked)

        failures, test_count = check_code(code)
        if failures:
            print("Packaging refused: checks failed in the staged code/ folder:")
            for failure in failures:
                print("  - " + failure)
            return 1
        print("Staged code/: contract test, %d tests and all scenarios passed." % test_count)

        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        zip_path = out / name
        build_zip(zip_path, staging)

    with zipfile.ZipFile(str(zip_path)) as archive:
        entries = [e for e in archive.infolist() if not e.is_dir()]
        top = sorted({e.filename.split("/")[0] for e in entries})
        print("\nWrote %s (%s)" % (zip_path, _human(zip_path.stat().st_size)))
        print("Top level: %s" % ", ".join(top))
        for entry in entries:
            if "/" not in entry.filename or entry.filename.startswith("code/logs/"):
                print("  %-60s %10s" % (entry.filename, _human(entry.file_size)))
        print("  ... %d files in total" % len(entries))
    if video.stat().st_size > 400 * 1024 * 1024:
        print("Warning: the video is larger than 400 MB; compress it (see video/script.md) if Moodle refuses the upload.")
    print("\nNext: open the zip, check it, upload it to Moodle before the deadline, and keep the confirmation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
