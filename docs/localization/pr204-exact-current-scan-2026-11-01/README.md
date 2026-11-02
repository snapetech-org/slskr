# PR #204 exact-current populated-catalog status

This reproducible scan reconciles exact translation evidence at catalog head `267269fc7179e9445efae7ab2ed66ac95fce9a5e` / tree `9f17ede96f077d66dfcfbe4ba7766dbf35f750db` with all 65,244 direct catalog cells. The latest catalog application is the same commit; source/runtime context remains `7ff454828398de6a3cfb72fe7f0ed21fe419425b` / tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`.

All catalog values are populated, with no missing keys, nulls, or blanks. Current exact-cell statuses are **23,865 accepted, 519 corrected, 10,541 correction-needed, 289 held, zero conflicts, and 30,030 unreviewed** across 5,437 source IDs. The scan covered 954 evidence files and honored 103 exact supersession references across 25 conflict/status reconciliation rows. Evidence-input manifest SHA-256: `3bf4b8decdd85420bce6ce4fd4be28d579740f6770fc1c1106c90c3cd9c7a16f`.

Per-locale unreviewed cells: ar 2,959, de 3,151, es 2,972, fr 3,022, hi 2,937, id 2,979, ja 2,002, ko 2,000, pt-BR 2,002, vi 2,002, zh-Hans 2,002, zh-Hant 2,002. The next contiguous semantic window is source indices 383–402.

The source-linked rollout target remains 6,588 translation cells and its source audit is complete. Whole-catalog review continues; 30,030 populated cells are unreviewed and 10,541 exact current values remain marked correction-needed. No release or tag was cut.

- `exact-current-scan.json` records catalog hashes, evidence input paths/sizes/hashes, per-locale counts, conflicts, and the first 100 unreviewed source IDs. SHA-256: `b1bc05309c1e80f935fed0fd404d0629284066daa16a70b93087da59f3b79866`.
- `scan_exact_current.py` reruns reconciliation against the frozen audit archive and exact evidence head. It recognizes reviewed final-target hashes and supersedes only cited exact records.

Example from the repository root:

```sh
python3 docs/localization/pr204-exact-current-scan-2026-11-01/scan_exact_current.py \
  --repo "$PWD" \
  --prior-audit /path/to/slskr-populated-catalog-review-7ff45482-20261101 \
  --head 267269fc7179e9445efae7ab2ed66ac95fce9a5e \
  --head-tree 9f17ede96f077d66dfcfbe4ba7766dbf35f750db \
  --source-head 7ff454828398de6a3cfb72fe7f0ed21fe419425b \
  --source-tree 9e9f2aa743c4ff3236af8f99619803bdc3a37152 \
  --output /path/to/task-scratch/pr204-exact-current-scan.json
```

The scan pins its evidence head; later documentation-only changes under `docs/localization` do not change the scanned `docs/pr-evidence` corpus.
