# Root cross-review: source indices 203–222

The parent independently checked all 86 exact-hash corrections from the 203–222 application against the exact source and caller context. The retained ledger has 85 `accepted-applied-target` rows and one `refined` row, with zero holds and zero source/old-target/applied-target hash mismatches. The exact root ledger SHA-256 is `8634de78c160b0cba6f5309ff02baaa30451fff02a2272cc85dcaea676ff2d14`; its one-row apply plan SHA-256 is `9067e22a39b6135de4f5fdb79b75e2f567c5fdad78e9c2e73a88bc1187ff01c8`.

The single refinement is Arabic `Adversarial Profile`. The 86-row application commit `cea8830` is unchanged and its original evidence ledger remains byte-for-byte intact. After the separate pt-BR #195 cross-review commit `44333cff`, Arabic `ملف تعريف التهديدات العدائية` (SHA-256 `00b475df8de53ae5d286ee9bcffb88263226a80a06a46ef477c5bb275ba10f37`) was refined in its own catalog commit `fdbf906cc1cf51015f0fa89a931c8619bc3907ee` / tree `e34cfbcec862c477ba65633db46313e564e99896` to `ملف تعريف أمان لمواجهة التهديدات` (SHA-256 `b4c40cdc2c6954e2975cce34a18c6069b2cb2f4da533ea22dee86f5f846175ef`). The root reviewer’s caller-specific rationale is preserved in the copied plan and ledger.

`refinement.jsonl` records the exact current target, new target, source, and application hashes. `verify_root_cross_review.py` checks all 86 rows against the pinned original catalog application, confirms 85/1/0 dispositions, verifies the one-cell follow-up diff, and ensures the current Arabic catalog contains the refined text. The original 86-row `applied-corrections.jsonl` is not modified.

Native-speaker approval is not claimed. No release or tag was made.

Run from the PR worktree:

```sh
python3 docs/pr-evidence/pr204-semantic-review-2026-11-01/root-cross-review-203-222-follow-up-2026-11-02/verify_root_cross_review.py \
  --repo "$PWD" \
  --prior-audit /path/to/slskr-populated-catalog-review-7ff45482-20261101
```
