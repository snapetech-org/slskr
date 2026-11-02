# Independent semantic review: source indices 103–122

This bundle reviews 20 source IDs (240 populated locale cells) at exact PR #204 head `f4d295b2df50fbce0d56c7b0b94b35ea87211d36` / tree `332e09992fd20eb5b0183a77be627732629edca7`. The runtime source context is pinned at `7ff454828398de6a3cfb72fe7f0ed21fe419425b` / tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`; catalog values are rehashed at the exact review head, which already contains 11 previously audited exact-hash corrections.

The 240 cells partition into 71 fresh decisions (64 accepted, 7 correction-needed), 117 exact accepted carries, and 52 exact prior correction-needed exclusions. There are no conflicts. All 12 locale values are present in the selection; the 71 fresh cells are the ones without an exact source/locale/source-hash/current-target-hash terminal disposition.

## Correction review

The correction proposals are in `manifest.json` and exact per-cell `decisions.jsonl`. Four proposals are high confidence and are eligible for exact-hash application after this evidence commit: German `Accept Join`, French `Accept Join`, German `Accept Join Request`, and Spanish `Accept Join Request`. Three proposals are moderate confidence and remain unapplied: Spanish/Hindi/Indonesian `Accept Join`. The verifier checks proposal/current hashes, context pins, overlap results, all 240 selected values, and bundle checksums.

No placeholders or ICU messages occur in the fresh cells. `AcoustID` and `URL` are retained where source context treats them as protected literals. This is an independent machine semantic review, not native-speaker approval. No source/catalog edits, tests/build/CI, or browser recapture were made during this evidence pass.

## Evidence files

- `selection.jsonl`: all 240 source/locale cells and their exact hashes/dispositions.
- `decisions.jsonl`: all 71 fresh per-cell decisions, notes, context, and proposals.
- `carries.jsonl`: 117 exact accepted carries.
- `terminal-exclusions.jsonl`: 52 exact correction-needed exclusions.
- `conflict-holds.jsonl`: empty; no conflicts in this window.
- `prior-evidence-scan-manifest.jsonl`: 740 rehashed prior evidence inputs.
- `source-context.txt`: pinned runtime snippets and per-key context.
- `manifest.json`, `verify_batch.py`, and `SHA256SUMS`: hashes, counts, and reproducible verifier.

Run from a worktree containing the pinned source and review commits:

```sh
python3 verify_batch.py --repo /path/to/slskR-worktree --prior-audit /path/to/slskr-populated-catalog-review-7ff45482-20261101
```
