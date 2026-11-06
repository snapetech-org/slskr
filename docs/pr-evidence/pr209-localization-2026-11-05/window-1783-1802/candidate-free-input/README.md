# slskR PR #209 W1783–W1802 candidate-free input

Pinned to open draft PR #209 at `0264a4fcaa944fee61049efec0cf3c451416c8b9` / tree `895e57c178d959a23aceddead27623f2dd854ba0`, branch `codex/slskr-l10n-audit-20261104-resync`, base `main` at `1bbaec9fdc63a86de343e37e33bae70d44301a36`. Before and after extraction, the local clone, branch ref, pull ref, PR head, and tree matched these pins. The live remote main SHA is captured separately because it differs from the PR API base SHA; this does not alter the pinned PR head or its reported base. See `attestation-before.json` and `attestation-after.json`.

This packet covers sorted source positions 1783–1802: 20 keys × 12 locales = 240 cells. The complete 5,441-key source queue matches the prior sealed W1763–W1782 candidate-free queue by exact bytes; this window follows it with no gap or overlap.

Active hold continuity: `1719::id` is preserved as hash-only; target hash unchanged=True, caller-context hash unchanged=True. See `active-hold-reattestation.jsonl`.

The exact quoted-literal scan covered 324 tracked production JavaScript/TypeScript files and found 29 caller references / 29 occurrences in 8 caller files. Callerless source positions: none. **Every target for a callerless position is hash-only:** its string is omitted from `current-target-cells.jsonl`, its target SHA-256 is retained, and the position is recorded in `caller-resolution-holds.jsonl`. These rows are holds, not reviewable translation proposals.

The prior W1763–W1782 packet’s 240 target readbacks are reattested at this head by hash only in previous-window-readback-reattestation-hash-only.jsonl; no prior or current target strings are copied into that lineage file. For caller-backed cells in this window, the packet records current target text, target hash, exact catalog path/file SHA/Git blob, placeholder/markup/numeric/protected-literal signatures, and a pinned caller-context SHA. Caller contexts contain source lines ±4 lines plus file byte count, file SHA-256, and Git blob. `localization-runtime-context.json` pins locale lookup and placeholder-formatting context to the same exact source tree. No review decisions or candidate proposals are included.

Offline integrity check: `python3 verify_candidate_free.py`. It checks the candidate-free input checksums, exact window coverage, catalog/source/caller pins, and hash-only active hold. It makes no network requests.
