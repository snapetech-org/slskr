# slskR PR #209 W1743–W1762 candidate-free input

Pinned to open draft PR #209 at `ccbc3dc721c1cbd225d4e512f4f0af4c80476620` / tree `075d1b72a2fd080404ebec19d354cb863638df21`, branch `codex/slskr-l10n-audit-20261104-resync`, base `main` at `1bbaec9fdc63a86de343e37e33bae70d44301a36`. Before and after extraction, the local clone, branch ref, pull ref, PR head, and tree matched these pins. See `attestation-before.json` and `attestation-after.json`.

This packet covers sorted source positions 1743–1762: 20 keys × 12 locales = 240 cells. The complete 5,441-key queue matches the prior sealed W1723–W1742 candidate-free queue by exact bytes; this window follows it with no gap or overlap.

Active hold continuity: `1719::id` is preserved as hash-only; target hash unchanged=True, caller-context hash unchanged=True. See `active-hold-reattestation.jsonl`.

The exact quoted-literal scan covered 324 tracked production JavaScript/TypeScript files and found 28 caller references / 28 occurrences in 19 caller files. Callerless source positions: [1754, 1755]. **Every target for a callerless position is hash-only:** its string is omitted from `current-target-cells.jsonl`, its target SHA-256 is retained, and the position is recorded in `caller-resolution-holds.jsonl`. These rows are holds, not reviewable translation proposals.

For caller-backed cells, the packet records current target text, target hash, exact catalog path/file SHA/Git blob, placeholder/markup/numeric/protected-literal signatures, and a pinned caller-context SHA. Caller contexts contain source lines ±4 lines plus file byte count, file SHA-256, and Git blob. `localization-runtime-context.json` pins locale lookup and placeholder-formatting context to the same exact source tree. No review decisions or candidate proposals are included.

Offline integrity check: `python3 verify_candidate_free.py`. It checks the candidate-free input checksums, exact window coverage, catalog/source/caller pins, and hash-only active hold. It makes no network requests.
