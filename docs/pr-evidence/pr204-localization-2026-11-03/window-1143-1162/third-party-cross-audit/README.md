# Third-party cross-audit — slskR PR #204 W1143–W1162

## Pins and integrity

- Live PR API and `refs/pull/204/head`: `20c66f7889c564fae5db1128d7dde22b512fc5be`; exact worktree tree: `85e82d73c6c191ea4875850d3c1afff7bae5c63a`. Worktree remained clean.
- Reconciled the candidate-free input, primary ledger, and blind ledger: 240/240 position-locale keys match; all 20 source IDs and all 12 locales are covered.
- Input, primary, and blind package checksums passed. Primary ledger SHA-256: `c69519b3c937516e3ba61d20fd810bab5451196822b4ac831ea657300b9bcaec`. Blind ledger SHA-256: `50062cff7ab0897284fb5b25dd4b9f3f2771a715d4831aae415cdf4b692b0522`.
- Recomputed source and current-target hashes for all 240 rows. Each current value also matches its locale catalog at the pinned worktree; all 12 catalog hashes/blobs match the input pins.
- Verified all 67 caller references against pinned source file hashes, Git blobs, and exact line text. The primary ledger stores direct-localized references only; those match the direct subset of the packet. The blind ledger’s full locations match all references.
- Placeholder and primary protected-literal checks passed across current values, primary candidates, blind proposals, and final recommendations. The 36 protected-literal occurrences are preserved.
- Numeric metadata differs at position 1145: the input numeric-token array is empty for the spelled-out “five-second,” while the primary ledger records `five-second`. Manual comparison confirms that every current and reviewed candidate preserves five seconds in all 12 locales; no quantity loss was found.

## Adjudication

- Recommendations: `186` accept-current, `28` primary candidate, `7` blind proposal, `4` converged proposal, `1` third-party refinement, `14` hold.
- Exact holds: 1146:ar, 1146:de, 1146:es, 1146:fr, 1146:hi, 1146:id, 1146:ja, 1146:ko, 1146:pt-BR, 1146:vi, 1146:zh-Hans, 1146:zh-Hant, 1160:zh-Hans, 1160:zh-Hant.
- At position 1146, both ledgers hold all locales because no direct localized caller is pinned; retain the hold.
- At position 1160, hold zh-Hans and zh-Hant: the current 主 ID may mean “main ID,” while the primary 主版本 ID may still misname Discogs Master. The pinned caller supplies only the field label, not a glossary.
- The primary rationale at position 1160 says the caller accepts either ID. The pinned snippet is only `label={interfaceText("Discogs Release/Master ID")}`; it does not establish API acceptance behavior. The audit uses only the wording in the label.
- Other disagreements are adjudicated cell-by-cell in `third-party-decisions.jsonl`, including the alternate French/Hindi W1144 candidates, W1145 crossfade wording, W1147 Web UI wording, W1150 automation-recipe terminology/discoverability, Korean W1154, discography labels, Vietnamese W1158, and Chinese W1162 feed wording.

## Limits

This is machine-assisted semantic review, not native-speaker approval. The proposed target values are recommendations only. No repository/catalog edits, tests, builds, scans, CI dispatches, workflow edits, PR edits, or Git delivery actions were performed.

## Output checksum

- `third-party-decisions.jsonl`: `4e3272a23846deb1aef325c09aa71c8b795a7947b4af42155f929034c37cd080`
