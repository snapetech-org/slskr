# slskR PR #204 semantic review: source indices 5400–5419

This batch reviews the exact current target values for 20 lexical source IDs across 12 locales. Its current PR/evidence head is `e05f1b71618bfecd89659b9387a6a6b224aa6e74` (tree `edf233c33dec6acea2ecf4fecb15edc13a75ee69`). The direct catalog/source snapshot is `7ff454828398de6a3cfb72fe7f0ed21fe419425b` (tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`); PR changes after that snapshot are documentation/evidence only. All 12 locale catalog hashes and runtime context source hashes are pinned in `manifest.json`.

## Exact accounting

The 20 keys have 240 populated locale cells. Exact overlap scanning across 627 archived JSONL inputs found 144 existing terminal dispositions; the remaining 96 cells had no exact source/locale/source-hash/target-hash terminal match.

- Fresh: 72 contextful cells reviewed; 39 accepted and 33 correction-needed. The other 24 fresh cells are held because their source strings have no runtime caller in the pinned non-locale code.
- Prior exact dispositions: 74 accepted carries, 46 correction-needed exclusions, and 24 held exclusions.
- Combined window disposition: 113 accepted, 79 correction-needed, and 48 held = 240 populated cells.

The prior exclusions and carries are listed in `terminal-exclusions.jsonl` and `carries.jsonl`; newly reviewed cells and any proposed wording are in `decisions.jsonl`. `selection.jsonl` contains the full 20 × 12 partition. No proposed translation is applied to a catalog in this batch. There are no pending exact terminal overlaps and no conflicting prior terminal statuses.

At the pinned snapshot, the catalogs contain 65,244 slots and all 65,244 are populated. Arabic has 15 structured plural-form maps (`zero`, `one`, `two`, `few`, `many`, `other`), each with non-empty localized strings; they are plural translations, not blanks. The earlier 65,229 figure counted only scalar values and excluded those 15 valid maps. This is the direct catalog census at `e05f1b7`, not a cumulative review count.

## Review scope and limits

The new semantic review covers all 12 locales for each selected cell through fresh decisions and exact prior dispositions. Runtime callers and nearby behavior were pinned for the 12 contextful source IDs in `source-context.txt`. Four other source strings (`5400`, `5403`, `5406`, `5413`) had no literal caller in `web/src` runtime JS/TS when searched with locale catalogs and test/spec files excluded; all 48 locale cells remain held until their UI placement is known.

Placeholder sets match for every fresh source, target, and correction proposal. No ICU messages were present. The Discovery Graph `→`/`·` and album-candidate `·`/`%` markers were checked. Arabic mirrors the route arrow as `←`, following the existing Arabic “Open System → Options” route-label translation documented with its target and catalog hashes in `source-context.txt` and `manifest.json`.

Confidence is per-cell in `decisions.jsonl`; this is an independent machine semantic review and has no native-speaker approval. The 33 correction proposals are suggestions only. The prior 12-locale browser captures remain applicable because no catalog or UI source was changed; this batch itself makes no claim of visual verification.

## Reverification

Run from a slskR checkout containing the pinned commits and the retained read-only overlap archive:

```sh
python3 docs/pr-evidence/pr204-semantic-review-2026-11-01/independent-5400-5419-all-12-locales/verify_batch.py \
  --repo "$PWD" \
  --prior-audit /mnt/disks/scratch/task-worktrees/localization-20261030/slskr-populated-catalog-review-7ff45482-20261101
```

The verifier checks commit/tree and catalog pins, the 65,244-cell census and Arabic plural-form maps, all selected live targets, placeholder/protected-literal checks, source context and the Arabic RTL precedent, repeats the four contextless searches, rehashes and rescans every exact-overlap input, validates the disjoint accounting, and verifies `SHA256SUMS`. The archive path above is task scratch and is intentionally retained read-only; its exact input file hashes are recorded in `prior-evidence-scan-manifest.jsonl`.

No tests, builds, CI, workflows, release actions, tags, or catalog/source edits were made for this review batch.
