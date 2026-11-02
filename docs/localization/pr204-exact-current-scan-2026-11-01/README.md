# PR #204 exact-current catalog status scan

This reproducible scan reconciles terminal semantic evidence against all 65,244 direct catalog cells at evidence head `5e60557627c148475d9ba753acdcc83fd8027b85` / tree `a01cf45e07dc21c62bc3ac7c7fa5e48268fc5063`. The latest catalog application is `af582e74c5c020e267dd8945e1e70bb4be745f0f` / tree `1f4b4bcfc48ef7dfebbfa4ab1eb97e68437ab640`; source/caller context is `7ff454828398de6a3cfb72fe7f0ed21fe419425b` / tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`. The scan covered 876 evidence files and honored 97 exact supersession references across 25 conflict/status reconciliation rows.

All 65,244 catalog values are populated; no keys, nulls, or blanks are missing. Exact-current statuses: **23,648 accepted, 333 corrected, 10,698 correction-needed, 289 held, zero conflicts, and 30,276 unreviewed** across 3,669 source IDs. The evidence-input manifest SHA-256 is `ef8f47c8ede572c774e6c9387eca12e534f1102ba361f9a13ea713ce5b073266`.

Per-locale unreviewed counts: ar 3,000; de 3,191; es 3,011; fr 3,064; hi 2,979; id 3,019; ja 2,002; ko 2,002; pt-BR 2,002; vi 2,002; zh-Hans 2,002; zh-Hant 2,002. The next disjoint semantic window is source indices 303–322.

- `exact-current-scan.json` records catalog hashes, every evidence input path/size/hash, per-locale totals, conflicts, and the first 100 unreviewed source IDs. SHA-256: `1e5fb021d66f2a3a52c7a505850d84a89ec3f68601fbe192c7ab8c98ea3690e5`.
- `scan_exact_current.py` reruns the reconciliation against the frozen audit archive and exact PR evidence head.

Example from the repository root:

```sh
python3 docs/localization/pr204-exact-current-scan-2026-11-01/scan_exact_current.py \
  --repo "$PWD" \
  --prior-audit /path/to/slskr-populated-catalog-review-7ff45482-20261101 \
  --head 5e60557627c148475d9ba753acdcc83fd8027b85 \
  --head-tree a01cf45e07dc21c62bc3ac7c7fa5e48268fc5063 \
  --source-head 7ff454828398de6a3cfb72fe7f0ed21fe419425b \
  --source-tree 9e9f2aa743c4ff3236af8f99619803bdc3a37152 \
  --output /path/to/task-scratch/pr204-exact-current-scan.json
```

The scan report pins its evidence head; subsequent documentation-only changes under `docs/localization` do not change the scanned `docs/pr-evidence` corpus. No tests, builds, CI, workflow changes, releases, or tags were part of this scan.
