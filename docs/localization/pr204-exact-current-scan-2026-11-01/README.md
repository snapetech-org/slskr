# PR #204 exact-current populated-catalog status

The exact-current scan is pinned to catalog head `ad7c283dfe84f31b52f5a27c363a605fe068e36c` / tree `d0a2faeba016b57850767fe0903b67621d61bc6c`. Source/runtime context remains `7ff454828398de6a3cfb72fe7f0ed21fe419425b` / tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`.

All 12 direct locale catalogs contain 65,244 populated cells across 5,437 source IDs; there are no missing keys, nulls, or blank targets. The scan covered 994 evidence files and honored 153 exact supersession references, including 25 conflict-resolution rows. Current unique-cell statuses are **23,980 accepted, 629 corrected, 10,435 correction-needed, 297 held, zero conflicts, and 29,903 unreviewed**. Evidence-input manifest SHA-256: `d05dc6b06d346040c8eda51d14415663802a5f2405c6164372dc74041d82bc23`.

Per-locale unreviewed cells: ar 2,936, de 3,129, es 2,951, fr 3,000, hi 2,919, id 2,958, ja 2,002, ko 2,000, pt-BR 2,002, vi 2,002, zh-Hans 2,002, zh-Hant 2,002. The next contiguous semantic window is 423–442; the first unreviewed source key is index 424 (`Average Score:`).

The source-linked 6,588-cell translation audit is complete. Whole-catalog populated-cell review continues; 29,903 populated cells remain unreviewed and 10,435 current cells remain correction-needed. Native-speaker approval is not claimed. No release or tag was cut.

`exact-current-scan.json` contains catalog hashes, evidence input paths/sizes/hashes, per-locale counts, conflicts, and the first 100 unreviewed source keys. SHA-256: `2dd308c827a680de148dcc1816a919050fd262aee859eeb4b0425b3c13c85b82`. `scan_exact_current.py` reruns the reconciliation against the frozen audit archive and exact catalog head. It recognizes exact-hash accepted-unchanged and held disposition ledgers and suppresses only their cited historical/provisional rows; every active cell status must still match current source and target hashes.

Example from the repository root:

```sh
python3 docs/localization/pr204-exact-current-scan-2026-11-01/scan_exact_current.py \
  --repo "$PWD" \
  --prior-audit /path/to/slskr-populated-catalog-review-7ff45482-20261101 \
  --head ad7c283dfe84f31b52f5a27c363a605fe068e36c \
  --head-tree d0a2faeba016b57850767fe0903b67621d61bc6c \
  --source-head 7ff454828398de6a3cfb72fe7f0ed21fe419425b \
  --source-tree 9e9f2aa743c4ff3236af8f99619803bdc3a37152 \
  --output /path/to/task-scratch/pr204-exact-current-scan.json
```
