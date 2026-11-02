# slskR PR #204 W843–W862 independent cross-review

Reviewed 180 cells across nine locales (Arabic, German, Spanish, French, Japanese, Korean, Brazilian Portuguese, Simplified Chinese, Traditional Chinese) at OPEN/DRAFT head `b52b7c9abd112328a70d9e811d3b6aa2d4feb8e6`, tree `d7a46bce75c76e3a74736b85175f7fa412324f39`. Source indices 842–861 are zero-based positions in the lexicographically sorted source keys; the pinned boundary keys are index 841 `Connected` and index 862 `Conservative Network`.

## Dispositions

- 133 exact current strings accepted.
- 36 of 37 primary proposals accepted.
- 1 primary proposal revised: French `Connection Timeout Milliseconds` uses “Délai d’attente de connexion (millisecondes)”.
- 10 missed current-string issues recorded as corrections: two Chinese count-prefix parentheses that pair with the hardcoded ASCII `)`; French hash values in the Mesh Peers subheader; and seven non-progressive live-search loading messages (ar, de, es, fr, ja, zh-Hans, zh-Hant).
- Holds: 0. All 180 `(sourceIndex, locale)` cells are unique and hash-pinned.

## Reattestation

All seven GitHub PR heads were queried at start and end; all stayed stable. slskR #204 remains OPEN/DRAFT at the requested head/tree. The task checkout was clean at the exact head/tree before and after. All 12 locale catalogs have 5,441 identical sorted keys; all 94 caller pins across 25 files reattest by file blob/hash, line hash, and recorded context lines. Every primary-ledger current/proposed hash was rechecked, then the assigned 180 current values and reviewed finals were independently recorded with exact SHA-256 hashes.

The prior `Connecting` and `Connection Failed` review records reattest for all 24 locales (18 of those rows belong to this nine-locale packet). Their review summary records base head `9d3aae249503d1732cc890a650052c85c57b2919` plus a dirty worktree with 12 modified catalog files. Those recorded working-file SHA-256 values match the catalog files captured in commit `aa106d2505de8c9ace2d7d6dbf2af9777651947d`; the 24 accepted target hashes also match the current PR catalog strings exactly. The evidence packet documents this boundary rather than treating the base tree itself as containing those keys.

`Connecting to Soulseek…` has no production text caller at this head. Its nine locale cells are reviewed as self-contained status strings only, with the caller gap retained in the evidence.

A separate completed packet covers Hindi, Indonesian, and Vietnamese: `/mnt/disks/scratch/task-scratch/slskr-pr204-window-0843-0862-crossreview-hidvi-20261102`. Its checksums were verified; it reports 60 cells, 14 accepted primary proposals, 43 accepted current values, 3 new correction candidates, and no holds.

## Limits and files

This is static semantic review. It does not claim native-speaker or headed-browser approval. No repository files changed, and no tests, builds, CI, or browser work ran. `crossreview-ledger.jsonl` has one exact-hash row per cell; `correction-candidates.jsonl` lists every revised cell. Caller, catalog, source, prior-review, live-PR, and worktree attestations are separate machine-readable files.
