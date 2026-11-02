# PR #204 exact-current catalog status scan

This reproducible scan reconciles terminal semantic evidence against all 65,244 direct catalog cells at evidence head `d0399855c23aa8dca9b92786c602d0be6ba9733b` / tree `d2cf82fc77e004c19b39df94edc307a24d766797`. The catalog application is `333df9a62f1a2d54186cc966ee0658b0c5d83de7` / tree `c4d442838f1932d7d3171a95944fb4ae94d7d2d2`; source/caller context is `7ff454828398de6a3cfb72fe7f0ed21fe419425b` / tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`. The scan covered 842 evidence files and honored 97 exact supersession references across 25 conflict/status reconciliation rows.

Unique exact-current statuses: **23,576 accepted, 276 corrected, 10,742 correction-needed, 289 held, 30,361 unreviewed**, with zero conflicts. The unreviewed cells span 3,685 source IDs. The evidence-input manifest SHA-256 is `fddfef5b9bee844d9108ea1700e1e553dd8aa55886dda404c76f7826105780e9`.

- `exact-current-scan.json` records catalog hashes, each evidence input path/size/hash, per-locale totals, conflicts, and the first 100 unreviewed source IDs. SHA-256: `c308a00cbef6661f380b04d2cbd9ff88466c9cc29f541e3ce18f7e5f8ca5afbf`.
- `scan_exact_current.py` reruns the reconciliation against the frozen audit archive and current PR evidence. It supports an exact evidence head/tree and source head/tree through command-line pins.

Example from the repository root:

```sh
python3 docs/localization/pr204-exact-current-scan-2026-11-01/scan_exact_current.py \
  --repo "$PWD" \
  --prior-audit /path/to/slskr-populated-catalog-review-7ff45482-20261101 \
  --head d0399855c23aa8dca9b92786c602d0be6ba9733b \
  --head-tree d2cf82fc77e004c19b39df94edc307a24d766797 \
  --source-head 7ff454828398de6a3cfb72fe7f0ed21fe419425b \
  --source-tree 9e9f2aa743c4ff3236af8f99619803bdc3a37152 \
  --output /path/to/task-scratch/pr204-exact-current-scan.json
```

The scan report pins its evidence head; subsequent documentation-only changes under `docs/localization` do not change the scanned `docs/pr-evidence` corpus. No tests, builds, CI, workflow changes, releases, or tags were part of this scan.
