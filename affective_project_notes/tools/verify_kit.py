"""Compare protected project-kit files with an original kit ZIP."""
import argparse
import hashlib
from pathlib import Path, PurePosixPath
import zipfile


PROJECT_ROOT = Path(__file__).resolve().parents[2] / "affective_project"
ZIP_PREFIX = "affective_project/"
PROTECTED_FILES = frozenset(
    (
        "README.md",
        "requirements.txt",
        "run_app.py",
        "run_scenario.py",
        "logs/README.txt",
        "tests/test_contract.py",
    )
)
PROTECTED_TREES = frozenset(("assets", "harness", "scenarios"))


def _is_protected(relative_path):
    parts = PurePosixPath(relative_path).parts
    if relative_path in PROTECTED_FILES:
        return True
    if not parts or parts[0] not in PROTECTED_TREES:
        return False
    return (
        "__pycache__" not in parts
        and PurePosixPath(relative_path).suffix not in (".pyc", ".pyo")
    )


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def verify(zip_path):
    """Return mismatches between protected ZIP entries and project files."""
    with zipfile.ZipFile(zip_path, "r") as archive:
        archive_files = {}
        for entry in archive.infolist():
            if entry.is_dir() or not entry.filename.startswith(ZIP_PREFIX):
                continue
            relative = entry.filename[len(ZIP_PREFIX) :]
            if _is_protected(relative):
                archive_files[relative] = entry

        project_files = {}
        for relative in PROTECTED_FILES:
            path = PROJECT_ROOT.joinpath(*PurePosixPath(relative).parts)
            if path.is_file():
                project_files[relative] = path
        for tree in PROTECTED_TREES:
            tree_root = PROJECT_ROOT / tree
            if not tree_root.exists():
                continue
            for path in tree_root.rglob("*"):
                if not path.is_file():
                    continue
                relative = path.relative_to(PROJECT_ROOT).as_posix()
                if _is_protected(relative):
                    project_files[relative] = path

        mismatches = []
        all_paths = sorted(set(archive_files) | set(project_files))
        for relative in all_paths:
            entry = archive_files.get(relative)
            path = project_files.get(relative)
            if entry is None:
                mismatches.append((relative, "missing from original ZIP"))
            elif path is None:
                mismatches.append((relative, "missing from project"))
            else:
                expected_hash = _sha256(archive.read(entry))
                actual_hash = _sha256(path.read_bytes())
                if expected_hash != actual_hash:
                    mismatches.append(
                        (
                            relative,
                            "SHA-256 differs (%s != %s)"
                            % (actual_hash, expected_hash),
                        )
                    )
        return mismatches, len(archive_files)


def main():
    parser = argparse.ArgumentParser(
        description="Verify protected kit files against the original ZIP."
    )
    parser.add_argument("zip_path", help="path to the original kit ZIP")
    arguments = parser.parse_args()
    mismatches, checked_count = verify(arguments.zip_path)
    if mismatches:
        print(
            "Protected kit check: %d mismatches across %d files."
            % (len(mismatches), checked_count)
        )
        for relative, reason in mismatches:
            print("%s: %s" % (relative, reason))
        return 1
    print(
        "Protected kit check: 0 mismatches across %d files." % checked_count
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
