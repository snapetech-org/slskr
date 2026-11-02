# PR #204 exact-current populated-catalog status

This reproducible scan reconciles semantic evidence against all 65,244 direct catalog cells at evidence head `a892d9735199dcd0f905498dba022e3e89f8ce9e` / tree `3dac36d064c52f79acea81b07c40ee12608e2349`. The latest catalog application is `a65ba4693c4f613f470509ab882f7532e40b11ef` / tree `f174eb839e00c23493c9a418392f589ad6d59597`; source/runtime context is `7ff454828398de6a3cfb72fe7f0ed21fe419425b` / tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`.

All 65,244 catalog values are populated; there are no missing keys, nulls, or blanks. Exact-current status counts are **23,782 accepted, 457 corrected, 10,589 correction-needed, 289 held, zero conflicts, and 30,127 unreviewed** across 3,642 source IDs. The scan covered 916 evidence files and honored 103 exact supersession references across 25 conflict/status reconciliation rows. Evidence-input manifest SHA-256: `52a5da26d8b11beb902886df065d9faf30d61c1e8f6f027eb4ca332cc4320ace`.

Per-locale unreviewed counts: ar 2,975; de 3,168; es 2,988; fr 3,038; hi 2,953; id 2,995; ja 2,002; ko 2,000; pt-BR 2,002; vi 2,002; zh-Hans 2,002; zh-Hant 2,002. The next disjoint semantic window is source indices 343–362.

The 6,588-cell source-linked rollout audit remains complete. Whole-catalog review has 30,127 populated cells still unreviewed and 10,589 current cells marked correction-needed. No release or tag was cut.

- `exact-current-scan.json` records catalog hashes, every evidence input path/size/hash, per-locale counts, conflicts, and the first 100 unreviewed source IDs. SHA-256: `f250ca922b6713cce6b20f75803475b79cc176c6fb0c6457a740c643db09f3a6`.
- `scan_exact_current.py` reruns reconciliation against the frozen audit archive and exact evidence head. It recognizes reviewed final-target hashes and supersedes only exact records cited by accepted-unchanged cross-review.

Example from the repository root:

```sh
python3 docs/localization/pr204-exact-current-scan-2026-11-01/scan_exact_current.py \
  --repo "$PWD" \
  --prior-audit /path/to/slskr-populated-catalog-review-7ff45482-20261101 \
  --head a892d9735199dcd0f905498dba022e3e89f8ce9e \
  --head-tree 3dac36d064c52f79acea81b07c40ee12608e2349 \
  --source-head 7ff454828398de6a3cfb72fe7f0ed21fe419425b \
  --source-tree 9e9f2aa743c4ff3236af8f99619803bdc3a37152 \
  --output /path/to/task-scratch/pr204-exact-current-scan.json
```

The scan pins its evidence head; later documentation-only changes under `docs/localization` do not change the scanned `docs/pr-evidence` corpus.
