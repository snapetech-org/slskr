# PR #204 exact-current populated-catalog status

This reproducible scan reconciles semantic evidence against all 65,244 direct catalog cells at evidence head `1471c2ff54e543f4409f43a0a8e2897d93448349` / tree `25092459c5e8c2bae28b7c762eb7e27db35ba775`. The latest catalog application is `39dc86982d73737832639483e7a6a6de74bee953` / tree `d232fada7fdf0da778117134ff371f2c2d45a0da`; source/runtime context is `7ff454828398de6a3cfb72fe7f0ed21fe419425b` / tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`.

All 65,244 catalog values are populated; there are no missing keys, nulls, or blanks. Exact-current status counts are **23,714 accepted, 410 corrected, 10,635 correction-needed, 289 held, zero conflicts, and 30,196 unreviewed** across 3,654 source IDs. The scan covered 892 evidence files and honored 97 exact supersession references across 25 conflict/status reconciliation rows. Evidence-input manifest SHA-256: `1933aca9142d98f9a25c11d4872d7238b8a6ec446750215974f1f28f742be031`.

Per-locale unreviewed counts: ar 2,987; de 3,178; es 2,999; fr 3,049; hi 2,965; id 3,006; ja 2,002; ko 2,002; pt-BR 2,002; vi 2,002; zh-Hans 2,002; zh-Hant 2,002. The next disjoint semantic window is source indices 323–342.

The 6,588-cell source-linked rollout audit remains complete. Whole-catalog review has 30,196 populated cells still unreviewed and 10,635 current cells marked correction-needed. No release or tag was cut.

- `exact-current-scan.json` records the catalog hashes, every evidence input path/size/hash, per-locale counts, conflicts, and the first 100 unreviewed source IDs. SHA-256: `ff0cbbd02db6537b168e358c7e3a36ad6929fb3e6dbbd09dc36a91977b327e21`.
- `scan_exact_current.py` reruns the reconciliation against the frozen audit archive and exact evidence head.

Example from the repository root:

```sh
python3 docs/localization/pr204-exact-current-scan-2026-11-01/scan_exact_current.py \
  --repo "$PWD" \
  --prior-audit /path/to/slskr-populated-catalog-review-7ff45482-20261101 \
  --head 1471c2ff54e543f4409f43a0a8e2897d93448349 \
  --head-tree 25092459c5e8c2bae28b7c762eb7e27db35ba775 \
  --source-head 7ff454828398de6a3cfb72fe7f0ed21fe419425b \
  --source-tree 9e9f2aa743c4ff3236af8f99619803bdc3a37152 \
  --output /path/to/task-scratch/pr204-exact-current-scan.json
```

The scan pins its evidence head; later documentation-only changes under `docs/localization` do not change the scanned `docs/pr-evidence` corpus.
