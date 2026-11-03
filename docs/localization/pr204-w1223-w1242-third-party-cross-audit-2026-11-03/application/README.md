# W1223–W1242 application and readback

This packet links the sealed candidate-free input, primary semantic ledger, independent blind ledger, and third-party cross-audit to the applied catalog commit.

- Exact catalog commit: `797f290a0478f3282755222ff4f714481a5db168` (tree `5194867bbffc981bd743dd092ed49b08648aa653`).
- The plan covers all 240 cells: 20 selected English keys × 12 direct locales.
- Final dispositions: 142 accept-current, 47 corrections, 27 refinements, and 24 holds.
- The 74 correction/refinement targets were checked against all 12 catalogs. The remaining 166 values were required to match their pinned current values.
- Readback found 240/240 expected values, zero changed non-target entries, unchanged ordered catalog keys, and all 24 no-caller holds unchanged.

`plan-240-cells.jsonl` records each pinned before-value, intended final value, disposition, hashes, and corresponding cross-audit row hash. `readback-240-cells.jsonl` records the live catalog value, hash, and change-state check for every cell. `summary.json` records the totals.

These are machine-assisted checks and review ledgers; they do not establish qualified native-speaker approval. The evidence does not approve a release. No build, test, scan, or CI workflow was run for this evidence-only commit.
