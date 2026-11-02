# PR #204 exact-current populated-catalog status

The exact-current reconciliation is pinned to catalog head `83aef2e22cede4041943bd0d612357e152e7a9b5` / tree `927bae235b4b57ac51a64389e6becadd75b133c3`. Source/runtime context remains `7ff454828398de6a3cfb72fe7f0ed21fe419425b` / tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`.

The 12 direct locale catalogs contain all 65,244 populated cells across 5,437 source IDs. There are no missing keys, nulls, or blank targets. Exact-current reconciliation scanned 969 evidence files and honored 103 exact supersession references across 25 reconciliation rows. Current unique-cell statuses are **23,910 accepted, 574 corrected, 10,492 correction-needed, 289 held, zero conflicts, and 29,979 unreviewed**. Evidence-input manifest SHA-256: `e4479934b1981fd5fc1173b7aa4230757a9ecb163b936e91547de63d5ca00b91`.

Per-locale unreviewed cells: ar 2,949, de 3,143, es 2,964, fr 3,013, hi 2,930, id 2,970, ja 2,002, ko 2,000, pt-BR 2,002, vi 2,002, zh-Hans 2,002, zh-Hant 2,002. The next contiguous source-key review window is 403–422.

The source-linked 6,588-cell translation audit is complete. Whole-catalog populated-cell review continues; the exact-current report identifies remaining unreviewed and correction-needed cells. Native-speaker approval is not claimed. No release or tag was cut.

- `exact-current-scan.json` contains catalog hashes, evidence input paths/sizes/hashes, per-locale counts, conflicts, and the first 100 unreviewed source keys. SHA-256: `e7414a131df1d3778875c7adc838d9f9a8ad3d6e032cf2226185d877249bec12`.
- `scan_exact_current.py` reruns the reconciliation against the frozen audit archive and exact catalog head. It matches evidence only when source and target hashes match the current catalogs.

Example from the repository root:

```sh
python3 docs/localization/pr204-exact-current-scan-2026-11-01/scan_exact_current.py \
  --repo "$PWD" \
  --prior-audit /path/to/slskr-populated-catalog-review-7ff45482-20261101 \
  --head 83aef2e22cede4041943bd0d612357e152e7a9b5 \
  --head-tree 927bae235b4b57ac51a64389e6becadd75b133c3 \
  --source-head 7ff454828398de6a3cfb72fe7f0ed21fe419425b \
  --source-tree 9e9f2aa743c4ff3236af8f99619803bdc3a37152 \
  --output /path/to/task-scratch/pr204-exact-current-scan.json
```
