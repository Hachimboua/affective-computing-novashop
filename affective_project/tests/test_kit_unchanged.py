"""Verify that the shared kit files remain unchanged from the Phase 0 baseline."""
import hashlib
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "harness": ("968afd3b5d9d683bb561d489255ddd284352abf285b8d94a15805986f401c1a3", 8),
    "run_app.py": "0f0fe8fb939a76fe8294f08f1c32ad15b6f3dd9e4d29072975926e64b91ac584",
    "run_scenario.py": "0c931063f45157b02174b3b3db192d18f23c474733da920ca3545e4868a12f9d",
    "scenarios": ("0635cf321f9218e6dc77a90e13ea106ea98b69be9fcaadb3c9653be8b5096e87", 8),
    "tests/test_contract.py": "d7dbc68bd337f59f26f397ea609989e0a13ae27a4053e184ae4aca1a54f00a47",
}


def _file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree_hash(relative_path):
    root = ROOT / relative_path
    files = sorted(
        (
            path
            for path in root.rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and path.suffix not in (".pyc", ".pyo")
        ),
        key=lambda path: path.relative_to(root).as_posix(),
    )
    manifest = "".join(
        "%s\t%s\n"
        % (path.relative_to(root).as_posix(), _file_hash(path))
        for path in files
    )
    return hashlib.sha256(manifest.encode("utf-8")).hexdigest(), len(files)


class KitUnchangedTests(unittest.TestCase):
    def test_protected_kit_files_match_phase0_checksums(self):
        for relative_path in ("harness", "scenarios"):
            with self.subTest(path=relative_path):
                self.assertEqual(_tree_hash(relative_path), EXPECTED[relative_path])

        for relative_path in ("run_app.py", "run_scenario.py", "tests/test_contract.py"):
            with self.subTest(path=relative_path):
                self.assertEqual(_file_hash(ROOT / relative_path), EXPECTED[relative_path])


if __name__ == "__main__":
    unittest.main(verbosity=2)
