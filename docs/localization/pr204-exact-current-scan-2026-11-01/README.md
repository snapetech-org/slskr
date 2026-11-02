# PR #204 exact-current populated-catalog status

The exact-current scan is pinned to catalog head `8885ff0dee176cd79169cdcc36e5e26b830054a6` / tree `fdf4893020e1f79c31c93eaecd737ad8d5aeae83`. Source/runtime context remains `7ff454828398de6a3cfb72fe7f0ed21fe419425b` / tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`.

All 12 direct locale catalogs contain 65,244 populated cells across 5,437 source IDs; there are no missing keys, nulls, or blank targets. The scan covered 1,009 evidence files and honored 153 exact supersession references, including 25 conflict-resolution rows. Current unique-cell statuses are **24,079 accepted, 661 corrected, 10,411 correction-needed, 297 held, zero conflicts, and 29,796 unreviewed**. Evidence-input manifest SHA-256: `a106e8eb119b77ed7a2e776cc96eaf916e910e466589412cd793a28b77b0a76c`.

Per-locale unreviewed cells: ar 2,917, de 3,112, es 2,934, fr 2,982, hi 2,900, id 2,941, ja 2,002, ko 2,000, pt-BR 2,002, vi 2,002, zh-Hans 2,002, zh-Hant 2,002. The next contiguous semantic window is 443–462; the first unreviewed source key is index 443 (`Avg Traversal Time:`).

The source-linked 6,588-cell translation audit is complete. Whole-catalog populated-cell review continues; 29,796 populated cells remain unreviewed and 10,411 current cells remain correction-needed. Native-speaker approval is not claimed. No release or tag was cut.

`exact-current-scan.json` contains catalog hashes, evidence input paths/sizes/hashes, per-locale counts, conflicts, and the first 100 unreviewed source keys. SHA-256: `2be42d252f95e9a148e72de66c9929ab241988a4d60447eca419b0a78bf93b00`. `scan_exact_current.py` reruns the reconciliation against the frozen audit archive and exact catalog head. It recognizes exact-hash accepted-unchanged and held disposition ledgers and suppresses only their cited historical/provisional rows; every active cell status must still match current source and target hashes.

Example from the repository root:

```sh
python3 docs/localization/pr204-exact-current-scan-2026-11-01/scan_exact_current.py \
  --repo "$PWD" \
  --prior-audit /path/to/slskr-populated-catalog-review-7ff45482-20261101 \
  --head 8885ff0dee176cd79169cdcc36e5e26b830054a6 \
  --head-tree fdf4893020e1f79c31c93eaecd737ad8d5aeae83 \
  --source-head 7ff454828398de6a3cfb72fe7f0ed21fe419425b \
  --source-tree 9e9f2aa743c4ff3236af8f99619803bdc3a37152 \
  --output /path/to/task-scratch/pr204-exact-current-scan.json
```
