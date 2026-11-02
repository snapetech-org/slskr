# PR #204 exact-current catalog status scan

This reproducible scan reconciles terminal semantic evidence against all 65,244 direct catalog cells at catalog application head `fdbf906cc1cf51015f0fa89a931c8619bc3907ee` / tree `e34cfbcec862c477ba65633db46313e564e99896`. It pins runtime/source context to `7ff454828398de6a3cfb72fe7f0ed21fe419425b` / tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`, scans 810 evidence files, and honors the 97 exact supersession references in the 25-cell conflict resolution. The scan includes the exact 183–202 and 203–222 window evidence plus the two explicit parent cross-review refinement addenda.

The unique exact-current statuses are **23,415 accepted, 168 corrected, 10,832 correction-needed, 289 held, 30,540 unreviewed**, and zero conflicts. The unreviewed cells span 3,719 source IDs. The evidence-input manifest SHA-256 is `98e622a8fb4166f3626082d3d0e578038f1f7238b7a76dfbf64356f017db894b`.

- `exact-current-scan.json` records catalog hashes, every evidence input path/size/hash, per-locale counts, conflicts, and the first 100 unreviewed source IDs. SHA-256: `7a6720dc464252132f65312de060f2568f621361dd3b62255df20853d42e8bbc`.
- `scan_exact_current.py` reruns the reconciliation against the same pinned catalog/source commits and current checked-in PR evidence.

Example from the repository root:

```sh
python3 docs/localization/pr204-exact-current-scan-2026-11-01/scan_exact_current.py \
  --repo "$PWD" \
  --prior-audit /path/to/slskr-populated-catalog-review-7ff45482-20261101 \
  --head fdbf906cc1cf51015f0fa89a931c8619bc3907ee \
  --head-tree e34cfbcec862c477ba65633db46313e564e99896 \
  --source-head 7ff454828398de6a3cfb72fe7f0ed21fe419425b \
  --source-tree 9e9f2aa743c4ff3236af8f99619803bdc3a37152 \
  --output /path/to/task-scratch/pr204-exact-current-scan.json
```

The scan report is pinned to the catalog application commit; later documentation commits do not change those catalog values. No tests, builds, CI, workflow changes, releases, or tags were part of this scan.
