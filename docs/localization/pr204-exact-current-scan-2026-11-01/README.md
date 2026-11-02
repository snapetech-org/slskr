# PR #204 exact-current populated-catalog status

This reproducible scan reconciles the exact translation evidence at head `e6d128e2ec47f6ce2fedca03505bf0c2312a959c` / tree `bccc76adfd26481457c562eca5d2d86fa24076d5` with all 65,244 direct catalog cells. The latest catalog application is `f10e8e62b4d8cc5249b8c31a42dcac060b555143` / tree `5df1b00dec1184f83618029e391ada2ad29de30d`; source/runtime context remains `7ff454828398de6a3cfb72fe7f0ed21fe419425b` / tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`.

All catalog values are populated, with no missing keys, nulls, or blanks. Current exact-cell statuses: **23,812 accepted, 479 corrected, 10,573 correction-needed, 289 held, zero conflicts, and 30,091 unreviewed** across 5,437 source IDs. The scan covered 942 evidence files and honored 103 exact supersession references across 25 conflict/status reconciliation rows. Evidence-input manifest SHA-256: `de98c00808fff6077e8f3f7d94fd38a7004f7b0cc1ea911e07afa395f05ca1c6`.

Per-locale unreviewed counts: ar 2,969, de 3,162, es 2,982, fr 3,032, hi 2,947, id 2,989, ja 2,002, ko 2,000, pt-BR 2,002, vi 2,002, zh-Hans 2,002, zh-Hant 2,002. The next contiguous semantic window is source indices 363–382.

The source-linked rollout target remains 6,588 translation cells and its source audit is complete. Whole-catalog review still has 30,091 populated cells unreviewed and 10,573 current cells marked correction-needed. No release or tag was cut.

- `exact-current-scan.json` records catalog hashes, evidence input paths/sizes/hashes, per-locale counts, conflicts, and the first 100 unreviewed source IDs. SHA-256: `1b686839725116d22d7832adf7da5115cb966abcd9d62cb012e9f4aebd2ab825`.
- `scan_exact_current.py` reruns reconciliation against the frozen audit archive and exact evidence head. It recognizes reviewed final-target hashes and supersedes only cited exact records.

Example from the repository root:

```sh
python3 docs/localization/pr204-exact-current-scan-2026-11-01/scan_exact_current.py \
  --repo "$PWD" \
  --prior-audit /path/to/slskr-populated-catalog-review-7ff45482-20261101 \
  --head e6d128e2ec47f6ce2fedca03505bf0c2312a959c \
  --head-tree bccc76adfd26481457c562eca5d2d86fa24076d5 \
  --source-head 7ff454828398de6a3cfb72fe7f0ed21fe419425b \
  --source-tree 9e9f2aa743c4ff3236af8f99619803bdc3a37152 \
  --output /path/to/task-scratch/pr204-exact-current-scan.json
```

The scan pins its evidence head; later documentation-only changes under `docs/localization` do not change the scanned `docs/pr-evidence` corpus.
