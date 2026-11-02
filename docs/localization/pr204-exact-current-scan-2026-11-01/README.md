# PR #204 exact-current catalog status scan

This reproducible scan reconciles terminal semantic evidence against all 65,244 direct catalog cells at evidence head `48211078d858e9dfbbc2fb2bc74d65cd54c58f0f` / tree `741d3be561eab466fcf5f79776d3e8350b2895e2`. The latest catalog application is `de509ead1789fe64811b14b63e1a22c14ade6893` / tree `e50004385568ab25e9d3eb5d314654880ef6ae8f`; source/caller context is `7ff454828398de6a3cfb72fe7f0ed21fe419425b` / tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`. The scan covered 858 evidence files and honored 97 exact supersession references across 25 conflict/status reconciliation rows.

All 65,244 catalog values are populated; no keys, nulls, or blanks are missing. Exact-current statuses: **23,598 accepted, 290 corrected, 10,731 correction-needed, 289 held, zero conflicts, and 30,336 unreviewed** across 3,680 source IDs. The evidence-input manifest SHA-256 is `f6dbcd12b6f5b0fa87af1ab8739ddafa77172e49f3d79e20c3500b8e0346a624`.

Per-locale unreviewed counts: ar 3,007; de 3,201; es 3,022; fr 3,075; hi 2,989; id 3,030; ja 2,002; ko 2,002; pt-BR 2,002; vi 2,002; zh-Hans 2,002; zh-Hant 2,002. The next disjoint source-key window is 283–302.

- `exact-current-scan.json` records catalog hashes, every evidence input path/size/hash, per-locale totals, conflicts, and the first 100 unreviewed source IDs. SHA-256: `2deb13947e32874bb74beec652d83c42dc899fa1b5ec35935f43637859159111`.
- `scan_exact_current.py` reruns the reconciliation against the frozen audit archive and exact PR evidence head.

Example from the repository root:

```sh
python3 docs/localization/pr204-exact-current-scan-2026-11-01/scan_exact_current.py \
  --repo "$PWD" \
  --prior-audit /path/to/slskr-populated-catalog-review-7ff45482-20261101 \
  --head 48211078d858e9dfbbc2fb2bc74d65cd54c58f0f \
  --head-tree 741d3be561eab466fcf5f79776d3e8350b2895e2 \
  --source-head 7ff454828398de6a3cfb72fe7f0ed21fe419425b \
  --source-tree 9e9f2aa743c4ff3236af8f99619803bdc3a37152 \
  --output /path/to/task-scratch/pr204-exact-current-scan.json
```

The scan report pins its evidence head; subsequent documentation-only changes under `docs/localization` do not change the scanned `docs/pr-evidence` corpus. No tests, builds, CI, workflow changes, releases, or tags were part of this scan.
