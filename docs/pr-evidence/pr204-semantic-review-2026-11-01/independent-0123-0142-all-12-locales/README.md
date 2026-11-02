# Independent semantic review: source indices 123–142

This bundle reviews 20 source IDs and all 240 populated locale cells at exact PR #204 catalog head `365677abe637fe720608fa05e8c250ea600deea0` / tree `b2e90645ec85eb04d907845f0d048eb78bed0005`. Runtime source context is pinned at `7ff454828398de6a3cfb72fe7f0ed21fe419425b` / tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`.

The window partitions into 82 fresh decisions (80 accepted, 2 correction-needed), 127 exact accepted carries, and 31 prior correction-needed exclusions, with no exact-status conflicts. All 12 values for every selected source key are retained in `selection.jsonl`; fresh review is limited to cells without a matching prior terminal record.

The two moderate proposals are Spanish `Active` → `Activo` and French `Active` → `Actif`. The shared source key labels both individual status rows and active-count statistics, so the plural/singular choice is context-dependent; neither is applied here. The 6 fresh translations for `Acquisition profile {profile}: {description}` preserve both placeholders. The exact runtime caller for this full template is absent at the pinned source head, which is called out in the evidence.

The verifier rehashes the exact source/catalog pins, all 749 prior evidence inputs, current values, overlaps, counts, placeholders, protected literals, and checksums. This is an independent machine semantic review, not native-speaker approval. No catalog/source edits, tests/build/CI, or browser recapture were made in this evidence pass.

## Evidence files

- `selection.jsonl`: all 240 current exact source/locale values and dispositions.
- `decisions.jsonl`: 82 fresh per-cell decisions.
- `carries.jsonl`: 127 exact accepted carries.
- `terminal-exclusions.jsonl`: 31 exact prior correction-needed exclusions.
- `conflict-holds.jsonl`: empty; no conflicts in this window.
- `prior-evidence-scan-manifest.jsonl`: 749 rehashed prior evidence inputs.
- `source-context.txt`, `manifest.json`, `verify_batch.py`, and `SHA256SUMS`: runtime context, pins, reproducible verification, and hashes.

Run from a worktree containing the pinned commits:

```sh
python3 verify_batch.py --repo /path/to/slskR-worktree --prior-audit /path/to/slskr-populated-catalog-review-7ff45482-20261101
```
