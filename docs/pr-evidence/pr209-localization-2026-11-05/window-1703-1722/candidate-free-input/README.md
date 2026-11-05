# slskR PR #209 W1703–W1722 candidate-free input

Pinned to open draft PR #209 at `91e109efba44ad9e53fe9544648a0d907a2bef77` / tree `38db78228144da5fc50179addccf826662bf97de`, branch `codex/slskr-l10n-audit-20261104-resync`, base `main` at `1bbaec9fdc63a86de343e37e33bae70d44301a36`. Before and after extraction, the local clone, branch ref, pull ref, PR head, and tree matched these pins. See `attestation-before.json` and `attestation-after.json`.

This packet covers sorted source positions 1703–1722: 20 keys × 12 locales = 240 cells. The complete 5,441-key queue matches the prior sealed W1683–W1702 candidate-free queue by exact bytes; this window follows it with no gap or overlap.

The exact quoted-literal scan covered 324 tracked production JavaScript/TypeScript files and found 30 caller references / 30 occurrences in 17 caller files. Callerless source positions: none. **Every target for a callerless position is hash-only:** its string is omitted from `current-target-cells.jsonl`, its target SHA-256 is retained, and the position is recorded in `caller-resolution-holds.jsonl`. These rows are holds, not reviewable translation proposals.

For caller-backed cells, the packet records current target text, target hash, exact catalog path/file SHA/Git blob, placeholder/markup/numeric/protected-literal signatures, and a pinned caller-context SHA. Caller contexts contain source lines ±4 lines plus file byte count, file SHA-256, and Git blob. `localization-runtime-context.json` pins locale lookup and placeholder-formatting context to the same exact source tree. No review decisions or candidate proposals are included.

Offline integrity check: `python3 verify_candidate_free.py --repo /home/keith/Documents/code/.task-worktrees/localization-20261105/slskr-w1683`. It checks packet checksums, full queue continuity, exact source/caller/catalog/runtime pins, text-free callerless values, all 240 cells, and saved before/after PR refs. It makes no network requests.
