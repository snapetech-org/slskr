## Merge

Use `main` as the target. Open a pull request only when current GitHub rules require one; push directly
when they allow it. Keep a pull request current with `main` only when those rules require it. Merge
after the checks and approvals required by current rules are satisfied. An explicit maintainer's
direction to merge is sufficient; no additional review or approval is required beyond those rules.
Use any merge method enabled in GitHub.

## Release Notes

<!--
  Add one validated fragment under release-notes/ for every user-facing,
  security, operational, or user-facing documentation change. See
  release-notes/README.md for the schema and preview command.
-->

- [ ] I added a release-note fragment under `release-notes/`.
- [ ] This change is internal-only and does not need a user-facing release note.
- [ ] I previewed the release text with `python3 scripts/release_notes.py preview`.

## Testing

Describe the validation performed for this change.
