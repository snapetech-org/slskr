#!/usr/bin/env python3
"""Regression tests for security scanner input selection."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("security-scan-inputs.py").resolve()


class SecurityScanInputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="slskr-scan-inputs-")
        self.root = Path(self.temporary.name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write(self, path: str, content: str = "fixture\n") -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def run_detector(self, mode: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), mode],
            cwd=self.root,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_trivy_selects_scanners_for_rust_source_and_workflows(self) -> None:
        self.write("Cargo.toml")
        self.write("crates/slskr/src/lib.rs")
        self.write(".github/workflows/ci.yml")

        result = self.run_detector("trivy")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "vuln,misconfig,secret")

    def test_semgrep_input_detection_does_not_depend_on_ripgrep(self) -> None:
        self.write("src/main.rs")

        result = self.run_detector("semgrep")

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_trivy_wrapper_scans_when_ripgrep_is_unavailable(self) -> None:
        scripts = self.root / "scripts"
        scripts.mkdir()
        shutil.copy2(SCRIPT, scripts / SCRIPT.name)
        shutil.copy2(
            SCRIPT.with_name("security-scan-local.sh"), scripts / "security-scan-local.sh"
        )
        self.write("Cargo.toml")
        self.write("crates/slskr/src/lib.rs")
        self.write(".github/workflows/ci.yml")

        fake_bin = self.root / "fake-bin"
        fake_bin.mkdir()
        fake_rg = fake_bin / "rg"
        fake_rg.write_text("#!/bin/sh\nexit 127\n", encoding="utf-8")
        fake_rg.chmod(0o755)
        scanner_args = self.root / "trivy-args.txt"
        fake_trivy = fake_bin / "trivy"
        fake_trivy.write_text(
            "#!/bin/sh\nprintf '%s\\n' \"$*\" > \"$TRIVY_TEST_ARGS\"\n",
            encoding="utf-8",
        )
        fake_trivy.chmod(0o755)

        environment = os.environ.copy()
        environment["PATH"] = f"{fake_bin}{os.pathsep}{environment['PATH']}"
        environment["TRIVY_TEST_ARGS"] = str(scanner_args)
        result = subprocess.run(
            ["bash", str(scripts / "security-scan-local.sh"), "--trivy-only", "--ci"],
            cwd=self.root,
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("scanners=vuln,misconfig,secret", result.stdout)
        self.assertEqual(
            scanner_args.read_text(encoding="utf-8").strip(),
            "fs --scanners vuln,misconfig,secret --timeout 20m --severity HIGH,CRITICAL "
            "--ignore-unfixed --exit-code 0 --skip-dirs .git --skip-dirs .local "
            "--skip-dirs node_modules "
            "--skip-dirs vendor --skip-dirs target --skip-dirs dist --skip-dirs build "
            "--skip-dirs coverage --skip-dirs .venv --config= --ignorefile= --secret-config= .",
        )

    def test_semgrep_wrapper_scans_when_ripgrep_is_unavailable(self) -> None:
        scripts = self.root / "scripts"
        scripts.mkdir()
        shutil.copy2(SCRIPT, scripts / SCRIPT.name)
        shutil.copy2(
            SCRIPT.with_name("security-scan-local.sh"), scripts / "security-scan-local.sh"
        )
        self.write("src/main.rs")

        fake_bin = self.root / "fake-bin"
        fake_bin.mkdir()
        fake_rg = fake_bin / "rg"
        fake_rg.write_text("#!/bin/sh\nexit 127\n", encoding="utf-8")
        fake_rg.chmod(0o755)
        scanner_args = self.root / "semgrep-args.txt"
        fake_uvx = fake_bin / "uvx"
        fake_uvx.write_text(
            "#!/bin/sh\nprintf '%s\\n' \"$*\" > \"$SEMGREP_TEST_ARGS\"\n",
            encoding="utf-8",
        )
        fake_uvx.chmod(0o755)

        environment = os.environ.copy()
        environment["PATH"] = f"{fake_bin}{os.pathsep}{environment['PATH']}"
        environment["SEMGREP_TEST_ARGS"] = str(scanner_args)
        result = subprocess.run(
            ["bash", str(scripts / "security-scan-local.sh"), "--semgrep-only"],
            cwd=self.root,
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Semgrep Community Edition", result.stdout)
        self.assertTrue(
            scanner_args.read_text(encoding="utf-8").startswith(
                "--from semgrep semgrep scan --config p/default"
            )
        )

    def test_ignored_docs_and_hooks_do_not_create_scan_inputs(self) -> None:
        self.write(".gitignore", "ignored/\n")
        self.write("ignored/Cargo.toml")
        self.write("docs/example.rs")
        self.write(".githooks/pre-commit.sh")
        self.write("README.md")

        trivy = self.run_detector("trivy")
        semgrep = self.run_detector("semgrep")

        self.assertEqual(trivy.returncode, 0, trivy.stderr)
        self.assertEqual(trivy.stdout.strip(), "")
        self.assertEqual(semgrep.returncode, 1, semgrep.stderr)

    def test_missing_git_context_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="slskr-no-git-") as non_repo:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "trivy"],
                cwd=non_repo,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("security scan input discovery failed", result.stderr)


if __name__ == "__main__":
    unittest.main()
