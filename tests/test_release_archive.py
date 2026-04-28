from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_PATH = REPO_ROOT / "releases" / "beta" / "delion-gigacode.zip"
REQUIRED_ARCHIVE_FILES = {
    "delion/gigacode-extension.json",
    "delion/GIGACODE.md",
    "delion/main.py",
    "delion/commands/deli/init.md",
    "delion/commands/deli/run.md",
    "delion/commands/deli/test.md",
    "delion/commands/deli/review.md",
    "delion/commands/deli/ci.md",
    "delion/orchestrator/cli.py",
    "delion/orchestrator/artifacts.py",
    "delion/orchestrator/models.py",
    "delion/orchestrator/validation.py",
}
FORBIDDEN_ARCHIVE_FILES = {
    "delion/orchestrator/agents.py",
    "delion/orchestrator/ci.py",
    "delion/orchestrator/ports.py",
    "delion/orchestrator/scm.py",
    "delion/orchestrator/workflow.py",
}


class ReleaseArchiveTests(unittest.TestCase):
    def test_beta_archive_contains_installable_extension(self) -> None:
        self.assertTrue(ARCHIVE_PATH.exists(), f"Archive not found: {ARCHIVE_PATH}")

        with zipfile.ZipFile(ARCHIVE_PATH) as archive:
            names = set(archive.namelist())

        self.assertTrue(REQUIRED_ARCHIVE_FILES.issubset(names))
        self.assertFalse(FORBIDDEN_ARCHIVE_FILES.intersection(names))
        self.assertFalse(any("__pycache__" in name for name in names))
        self.assertFalse(any(name.endswith((".pyc", ".pyo")) for name in names))

    def test_extracted_beta_archive_can_initialize_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            extension_root = root / "extensions"
            project_root = root / "project"
            extension_root.mkdir()
            project_root.mkdir()

            with zipfile.ZipFile(ARCHIVE_PATH) as archive:
                archive.extractall(extension_root)

            main_py = extension_root / "delion" / "main.py"
            result = subprocess.run(
                [
                    sys.executable,
                    str(main_py),
                    "--project-root",
                    str(project_root),
                    "\\deli:init",
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertTrue((project_root / "docs" / "system-requirements.md").exists())


if __name__ == "__main__":
    unittest.main()
