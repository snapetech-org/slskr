# PR #204 exact-current catalog status scan

This reproducible scan reconciles terminal semantic evidence against all 65,244 direct catalog cells at catalog application head `5d0156003b5805b27c78b1289722a64ab30234a8` / tree `b9b0b5fc9b4c6e971be0c4179606ef6687ceb4a7`. It pins source context to `7ff454828398de6a3cfb72fe7f0ed21fe419425b` / tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`, scans 826 evidence files, and honors 97 exact supersession references across 25 conflict/status reconciliation rows. It includes the independent 223–242 window review and root cross-review.

The unique exact-current statuses are **23,497 accepted, 193 corrected, 10,814 correction-needed, 289 held, 30,451 unreviewed**, and zero conflicts. The unreviewed cells span 3,703 source IDs. The evidence-input manifest SHA-256 is `67f47ac525a88cc31c1a7441d4c2f8da76ec977a9941a2dafb7b8d0eb189f0ee`.

- `exact-current-scan.json` records catalog hashes, each evidence input path/size/hash, per-locale totals, conflicts, and the first 100 unreviewed source IDs. SHA-256: `e2f0bbb010f4cae5a82f20efd2439e477db027abc3fdea9e1bf9b7d199fc4112`.
- `scan_exact_current.py` reruns the reconciliation against the frozen audit archive and current PR evidence.

Example from the repository root:

```sh
python3 docs/localization/pr204-exact-current-scan-2026-11-01/scan_exact_current.py \
  --repo "$PWD" \
  --prior-audit /path/to/slskr-populated-catalog-review-7ff45482-20261101 \
  --head 5d0156003b5805b27c78b1289722a64ab30234a8 \
  --head-tree b9b0b5fc9b4c6e971be0c4179606ef6687ceb4a7 \
  --source-head 7ff454828398de6a3cfb72fe7f0ed21fe419425b \
  --source-tree 9e9f2aa743c4ff3236af8f99619803bdc3a37152 \
  --output /path/to/task-scratch/pr204-exact-current-scan.json
```

The scan report is pinned to its catalog application commit; later documentation commits do not change those catalog values. No tests, builds, CI, workflow changes, releases, or tags were part of this scan.
