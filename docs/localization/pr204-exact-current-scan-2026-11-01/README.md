# PR #204 exact-current catalog status scan

This reproducible scan reconciles terminal semantic evidence against all 65,244 direct catalog cells at catalog application head `e3b1667bcec64e3b41c124e66ea6b29cc88102b9` / tree `baa6d9cb0a7683372c7a6130aa10147b0c880141`. It pins runtime/source context to `7ff454828398de6a3cfb72fe7f0ed21fe419425b` / tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`, scans 784 evidence files, and honors the 97 exact supersession references in the 25-cell conflict resolution.

The unique exact-current statuses are 23,317 accepted, 38 corrected, 10,957 correction-needed, 289 held, 30,643 unreviewed, and zero conflicts. There are 3,737 source IDs with at least one unreviewed locale cell. The evidence-input manifest SHA-256 is `6d0f20a4f88773121c3f20b3f644c8740560af242976214342eeeab51a6fe87b`.

- `exact-current-scan.json` records the catalog hashes, every evidence input path/size/hash, per-locale counts, conflict count, and first 100 unreviewed source IDs. SHA-256: `fa7191b87d9d845d10b46f40e84dce0f98035e2c6ee9528f79f9852360fdb457`.
- `scan_exact_current.py` reruns the reconciliation against the same pinned catalog/source commits and the current checked-in PR evidence directory.

Example from the repository root:

```sh
python3 docs/localization/pr204-exact-current-scan-2026-11-01/scan_exact_current.py \
  --repo "$PWD" \
  --prior-audit /path/to/slskr-populated-catalog-review-7ff45482-20261101 \
  --head e3b1667bcec64e3b41c124e66ea6b29cc88102b9 \
  --head-tree baa6d9cb0a7683372c7a6130aa10147b0c880141 \
  --source-head 7ff454828398de6a3cfb72fe7f0ed21fe419425b \
  --source-tree 9e9f2aa743c4ff3236af8f99619803bdc3a37152 \
  --output /tmp/pr204-exact-current-scan.json
```

The scan report is historical to the catalog application commit above; later documentation commits do not change the pinned catalogs. No tests, builds, CI, workflow changes, releases, or tags are part of this scan.
