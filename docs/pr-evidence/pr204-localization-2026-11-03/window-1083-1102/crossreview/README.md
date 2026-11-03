# W1083–W1102 adjudication proposal, revision 2

This checksum-sealed packet supersedes the unratified proposal at `/mnt/disks/scratch/task-scratch/slskr-pr204-w1083-1102-20261103/adjudication-proposal`. It compares the root strict-blind and private primary ledgers against the frozen clean input, then adds read-only render-path evidence for position 1095 at the exact pinned PR head. It remains an **unratified proposal**; no catalog, worktree, or PR changes have been applied.

## Pins and render evidence

- PR head/tree: `e1d9eb920ee121d8c108b098e94f0f3d2b440256` / `1d274f797f620482f4f344e7cf67de27e75e5568`
- Clean-input manifest SHA-256: `73af07cb20c3a1aca99456481bc8124ccc5b7fd81e404a365751e21dddcae818`
- Root strict-blind ledger SHA-256: `0b98666a81e962e18d79d6cfcd1a7a3afbbb83dee83e6b4d38d5ca20a9cf5fd4`
- Primary ledger SHA-256: `3b4faa3e52cafc9a2777566603f93eef699c472346fba84b91fd9e2c1b1ee45c`
- Render-path evidence SHA-256: `3100c56787b91d7b0896fe1db245b5c7056e7ee81c12c64ed964d90ebd6243c9`
- Source-order/window hashes: `dcabd0a1f1e6e9504a47b5126d9f9fbd10aa5a2da80266ab945098248b97d983` / `3938b39471c24139918902de990427089ea5b96f1a93bb7e793b8f7a52f00cd3`

`render-path-evidence.json` records `ShareGroups.jsx` → `TooltipButton.jsx` → `LocalizedPopup`; at the pinned head the popup defaults to translation and invokes `t(content, parameters)`. The same evidence records the Arabic catalog glossary. The current Arabic W1095 target follows established terms for shared collections and share groups, so all twelve W1095 cells use `accept-current` and none remain held.

## Review counts

- 240 cells: 20 source positions × 12 locales
- 83 cells have a primary/blind target or disposition disagreement
- 80 proposed target changes; final disposition counts: `{'correction': 51, 'accept-current': 136, 'hold-context': 24, 'refinement': 29}`
- 4 final targets and 4 final dispositions differ from the root blind ledger
- Positions 1090 and 1091 remain 24 caller-context holds

`adjudication.jsonl` contains all cells with current, root, primary, and selected final values and rationale. `discrepancies.jsonl` contains the 83 cells with primary/blind disagreements.
