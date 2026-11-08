#!/usr/bin/env python3

from __future__ import annotations

import shutil
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

import release_notes


VALID_NOTE = """---
category: fixed
audience: users, operators
area: release-pipeline
action: none
breaking: false
---
Release validation now publishes the same curated summary to GitHub and Discord so operators and users see consistent release details.
"""


class ReleaseNotesTests(unittest.TestCase):
    def test_workflow_summary_uses_only_the_requested_dated_changelog(self) -> None:
        root = Path(__file__).resolve().parent.parent
        step = (root / '.github/workflows/release.yml').read_text().split('      - name: Create release notes\n', 1)[1]
        script = textwrap.dedent(step.split('        run: |\n', 1)[1].split('          previous_tag=', 1)[0])
        for version, deferred, expected in (('2.4.6', 'false', 0), ('2.4.6', 'true', 0), ('2.4.7', 'false', 1)):
            with self.subTest(version=version, deferred=deferred):
                with tempfile.TemporaryDirectory(prefix='slskr-release-summary-') as directory:
                    fixture = Path(directory)
                    (fixture / 'release').mkdir()
                    (fixture / 'CHANGELOG.md').write_text(
                        '# Changelog\n\n## [Unreleased]\n\n## [2.4.6] — 2026-11-07\n\n'
                        '- Current portable runtime fix.\n\n## [2.4.5] — 2026-11-06\n\n- Older release detail.\n')
                    env = {**os.environ, 'RELEASE_VERSION': version, 'RELEASE_REPOSITORY': 'snapetech-org/slskr',
                           'RELEASE_REF_NAME': 'v' + version, 'DEFER_CHOCOLATEY_INITIAL_REVIEW': deferred}
                    result = subprocess.run(['bash', '-c', script], cwd=fixture, env=env,
                                            capture_output=True, text=True)
                    self.assertEqual(result.returncode, expected, result.stderr)
                    if expected == 0:
                        notes = (fixture / 'release/RELEASE_NOTES.md').read_text()
                        self.assertIn('Current portable runtime fix.', notes)
                        self.assertNotIn('Older release detail.', notes)
                        self.assertEqual('Chocolatey updates await' in notes, deferred == 'true')

    def test_release_validator_allows_a_product_placeholder_reference(self) -> None:
        validator = Path(__file__).with_name("validate-release-notes.sh")
        notes = """# slskr 1.0.0

## Highlights

- Shared directories now open through a labeled button instead of a placeholder link. Missing directory paths are shown as unavailable and cannot trigger an empty browse action.
"""
        with tempfile.TemporaryDirectory(prefix="slskr-release-validator-") as temporary:
            notes_path = Path(temporary) / "release-notes.md"
            notes_path.write_text(notes, encoding="utf-8")
            subprocess.check_call(["bash", str(validator), "1.0.0", str(notes_path)])

            for stub in ("- TODO: write this note", "- [placeholder]", "- placeholder"):
                with self.subTest(stub=stub):
                    notes_path.write_text(
                        f"# slskr 1.0.0\n\n## Highlights\n\n{stub}\n",
                        encoding="utf-8",
                    )
                    result = subprocess.run(
                        ["bash", str(validator), "1.0.0", str(notes_path)],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("placeholder or empty-release wording", result.stderr)

    def test_schema_and_formats(self) -> None:
        note = release_notes.parse_release_note("release-notes/pipeline.md", VALID_NOTE)
        self.assertEqual(note["errors"], [])
        self.assertIn("Release validation", note["body"])
        curated = release_notes.format_curated_notes([note])
        self.assertIn("### User-facing changes", curated)
        self.assertIn("#### Fixed", curated)
        self.assertIn("**Release Pipeline:**", curated)
        metadata = release_notes.format_capture_metadata([note])
        self.assertIn("### Capture metadata", metadata)
        self.assertIn("users, operators", metadata)

    def test_invalid_schema_is_rejected(self) -> None:
        note = release_notes.parse_release_note(
            "release-notes/incomplete.md",
            "---\ncategory: changed\n---\nTODO",
        )
        self.assertTrue(note["errors"])
        self.assertIn("placeholder", "\n".join(note["errors"]))

        html_comment = release_notes.parse_release_note(
            "release-notes/html-comment.md",
            VALID_NOTE.replace("action: none", "action: safe --!> action"),
        )
        self.assertIn("HTML comment", "\n".join(html_comment["errors"]))

    def test_range_discovery_assembly_and_append_only_guard(self) -> None:
        repository = Path(tempfile.mkdtemp(prefix="slskr-release-notes-"))
        try:
            self.run_git(repository, "init", "--initial-branch=main", "--quiet")
            self.run_git(repository, "config", "user.name", "Release Notes Test")
            self.run_git(repository, "config", "user.email", "release-notes@example.invalid")
            (repository / "release-notes").mkdir()
            (repository / "release-notes" / "README.md").write_text("# Release notes\n")
            self.run_git(repository, "add", ".")
            self.run_git(repository, "commit", "--quiet", "-m", "chore: initialize")
            base = self.run_git(repository, "rev-parse", "HEAD")
            script = Path(__file__).with_name("release_notes.py")
            opt_out_body = repository / "opt-out.md"
            opt_out_body.write_text("release-note: none\n")
            subprocess.check_call(
                [
                    sys.executable,
                    str(script),
                    "--cwd",
                    str(repository),
                    "check",
                    "--base",
                    base,
                    "--head",
                    base,
                    "--pr-body-file",
                    str(opt_out_body),
                ]
            )
            with self.assertRaises(subprocess.CalledProcessError):
                empty_body = repository / "empty-body.md"
                empty_body.write_text("")
                subprocess.check_call(
                    [
                        sys.executable,
                        str(script),
                        "--cwd",
                        str(repository),
                        "check",
                        "--base",
                        base,
                        "--head",
                        base,
                        "--pr-body-file",
                        str(empty_body),
                    ]
                )

            (repository / "release-notes" / "pipeline.md").write_text(VALID_NOTE)
            self.run_git(repository, "add", ".")
            self.run_git(repository, "commit", "--quiet", "-m", "chore: add release note")
            head = self.run_git(repository, "rev-parse", "HEAD")

            entries = release_notes.changed_release_note_files(base, head, repository)
            self.assertEqual(entries, [{"status": "A", "file": "release-notes/pipeline.md"}])
            notes, errors = release_notes.read_release_notes(entries, head, repository)
            self.assertEqual(errors, [])
            self.assertEqual(len(notes), 1)

            worktree_note = repository / "release-notes" / "worktree.md"
            worktree_note.write_text(VALID_NOTE.replace("Release validation", "Working-tree validation"))
            worktree_entries = release_notes.changed_release_note_files(
                head, "WORKTREE", repository
            )
            self.assertEqual(
                worktree_entries,
                [
                    {"status": "A", "file": "release-notes/worktree.md"},
                ],
            )
            worktree_notes, worktree_errors = release_notes.read_release_notes(
                worktree_entries, "WORKTREE", repository
            )
            self.assertEqual(worktree_errors, [])
            self.assertEqual(len(worktree_notes), 1)
            worktree_note.unlink()

            preview = subprocess.check_output(
                [
                    sys.executable,
                    str(script),
                    "--cwd",
                    str(repository),
                    "preview",
                    "--base",
                    base,
                    "--head",
                    head,
                ],
                text=True,
            )
            self.assertIn("### User-facing changes", preview)

            body = "# slskr 1.0.0\n\n## Highlights\n\n- Existing release detail.\n"
            body_path = repository / "release.md"
            body_path.write_text(body)
            summary_path = repository / "summary.md"
            subprocess.check_call(
                [
                    sys.executable,
                    str(script),
                    "--cwd",
                    str(repository),
                    "check",
                    "--base",
                    base,
                    "--head",
                    head,
                    "--pr-body-file",
                    str(body_path),
                    "--summary-file",
                    str(summary_path),
                ]
            )
            subprocess.check_call(
                [
                    sys.executable,
                    str(script),
                    "--cwd",
                    str(repository),
                    "assemble",
                    "--base",
                    base,
                    "--head",
                    head,
                    "--input",
                    str(body_path),
                    "--output",
                    str(body_path),
                ]
            )
            assembled = body_path.read_text()
            self.assertIn("### User-facing changes", assembled)
            self.assertIn("## Highlights\n\n### User-facing changes", assembled)

            (repository / "release-notes" / "pipeline.md").write_text(
                VALID_NOTE.replace("Release validation", "Changed release validation")
            )
            self.run_git(repository, "add", ".")
            self.run_git(repository, "commit", "--quiet", "-m", "chore: edit release note")
            edited_head = self.run_git(repository, "rev-parse", "HEAD")
            self.assertEqual(
                release_notes.changed_release_note_files(head, edited_head, repository),
                [{"status": "M", "file": "release-notes/pipeline.md"}],
            )
            with self.assertRaises(subprocess.CalledProcessError):
                subprocess.check_call(
                    [
                        sys.executable,
                        str(script),
                        "--cwd",
                        str(repository),
                        "check",
                        "--base",
                        head,
                        "--head",
                        edited_head,
                        "--pr-body-file",
                        str(body_path),
                    ]
                )
        finally:
            shutil.rmtree(repository)

    @staticmethod
    def run_git(repository: Path, *args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=repository, text=True).strip()


if __name__ == "__main__":
    unittest.main()
