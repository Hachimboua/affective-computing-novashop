"""Verify the project from an isolated temporary copy."""
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = WORKSPACE_ROOT / "affective_project"
ERROR_LINE = re.compile(r"(?m)^\s*(?:PROBLEMS|ERROR)\s*:")


def _run(command, cwd):
    return subprocess.run(
        command,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        timeout=300,
    )


def main():
    if not PROJECT_ROOT.is_dir():
        print("Clean-copy check failed: affective_project/ was not found.")
        return 1

    failed_checks = []
    scenario_count = 0
    scenario_passes = 0
    test_count = 0
    with tempfile.TemporaryDirectory(prefix="novashop-clean-copy-") as temp_dir:
        copied_project = Path(temp_dir) / "affective_project"
        shutil.copytree(
            PROJECT_ROOT,
            copied_project,
            ignore=shutil.ignore_patterns(
                ".git", ".venv", "venv", "env", "__pycache__"
            ),
        )

        contract = _run(
            [sys.executable, "tests/test_contract.py"], copied_project
        )
        if contract.returncode:
            failed_checks.append("contract test")

        tests = _run(
            [
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "tests",
            ],
            copied_project,
        )
        count_match = re.search(r"Ran (\d+) tests?", tests.stdout)
        test_count = int(count_match.group(1)) if count_match else 0
        if tests.returncode or not test_count:
            failed_checks.append("unit tests")
            failed_checks.extend(
                "unit test " + name
                for name in re.findall(
                    r"(?m)^(?:FAIL|ERROR): ([^\r\n]+)", tests.stdout
                )
            )

        scenario_root = copied_project / "scenarios"
        scenarios = sorted(scenario_root.rglob("*.json"))
        scenario_count = len(scenarios)
        if not scenarios:
            failed_checks.append("no scenarios found")

        logs_dir = copied_project / "logs"
        existing_logs = (
            {path.resolve() for path in logs_dir.iterdir() if path.is_file()}
            if logs_dir.is_dir()
            else set()
        )
        scenario_failures = []
        for scenario in scenarios:
            relative_path = scenario.relative_to(copied_project)
            result = _run(
                [sys.executable, "run_scenario.py", str(relative_path)],
                copied_project,
            )
            if result.returncode or ERROR_LINE.search(result.stdout):
                scenario_failures.append(relative_path.as_posix())
            else:
                scenario_passes += 1

        generated_logs = (
            [
                path
                for path in logs_dir.iterdir()
                if path.is_file() and path.resolve() not in existing_logs
            ]
            if logs_dir.is_dir()
            else []
        )
        for log_path in generated_logs:
            if ERROR_LINE.search(log_path.read_text(encoding="utf-8")):
                scenario_failures.append("log " + log_path.name)
            log_path.unlink()
        failed_checks.extend(
            "scenario " + name for name in scenario_failures
        )

    status = "PASS" if not failed_checks else "FAIL"
    print(
        "Clean-copy check (Python %s): %s; contract: %s; unit tests: %d; "
        "scenarios: %d/%d."
        % (
            platform.python_version(),
            status,
            "PASS" if "contract test" not in failed_checks else "FAIL",
            test_count,
            scenario_passes,
            scenario_count,
        )
    )
    if failed_checks:
        for failure in failed_checks:
            print("  Failed: " + failure)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
