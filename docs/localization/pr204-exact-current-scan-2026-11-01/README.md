# PR #204 exact-current catalog status scan

This reproducible scan reconciles terminal semantic evidence against all 65,244 direct catalog cells at catalog application head `cc55673a362e627e256dc45cd90c9fe5c28c163f` / tree `739ba38688b25d02002a6f044cb393b4996de836`. It pins runtime/source context to `7ff454828398de6a3cfb72fe7f0ed21fe419425b` / tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`, scans 794 evidence files, and honors the 97 exact supersession references in the 25-cell conflict resolution.

The unique exact-current statuses are **23,377 accepted, 82 corrected, 10,917 correction-needed, 289 held, 30,579 unreviewed**, and zero conflicts. The unreviewed cells span 3,726 source IDs. The evidence-input manifest SHA-256 is `671da42aab3c65c85b32dcafba14aa25b70ff63f60b0048ad6b5b1adf82f4764`.

- `exact-current-scan.json` records catalog hashes, every evidence input path/size/hash, per-locale counts, conflicts, and the first 100 unreviewed source IDs. SHA-256: `1dca9cb9bc9ecbc44b3d73ec9a4ca0dd0a69a10cfb8340969045f1a5f6716ce4`.
- `scan_exact_current.py` reruns the reconciliation against the same pinned catalog/source commits and current checked-in PR evidence.

Example from the repository root:

```sh
python3 docs/localization/pr204-exact-current-scan-2026-11-01/scan_exact_current.py \
  --repo "$PWD" \
  --prior-audit /path/to/slskr-populated-catalog-review-7ff45482-20261101 \
  --head cc55673a362e627e256dc45cd90c9fe5c28c163f \
  --head-tree 739ba38688b25d02002a6f044cb393b4996de836 \
  --source-head 7ff454828398de6a3cfb72fe7f0ed21fe419425b \
  --source-tree 9e9f2aa743c4ff3236af8f99619803bdc3a37152 \
  --output /path/to/task-scratch/pr204-exact-current-scan.json
```

The scan report is pinned to the catalog application commit; later documentation commits do not change those catalog values. No tests, builds, CI, workflow changes, releases, or tags were part of this scan.
