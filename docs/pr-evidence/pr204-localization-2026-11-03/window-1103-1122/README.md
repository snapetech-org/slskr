# slskR PR #204 localization review W1103–W1122

This packet records an exact-head review of 20 sorted source IDs across all 12 direct locales (240 cells), based on PR head `e45e6967625c5e804b688b9cb03d359ea59d000b` and tree `c5164178f16e0fa2f59586c9ab3685e1ac08dfa5`.

The frozen clean input, primary review, candidate-free independent review, and ratified adjudication are preserved in this directory. Root ratification approved 19 direct-caller changes, retained 115 current values, and held 106 cells. Holds include the 96 cells for eight IDs without a direct localized caller in the pinned input, four unresolved Swarm terminology cells, and six wording disagreements requiring qualified native-speaker review.

`apply-plan.json` contains only the 19 approved changes. `apply_ratified_window.py` checks the exact baseline commit, all twelve catalog file and Git blob pins, the ratified ledger, and every reviewed cell before applying those changes. `readback.json` records the final value and hash of all 240 cells, changed-catalog hashes, and ordered-key checksums.

Primary and blind checksum manifests are nested in their respective folders. The top-level `SHA256SUMS.txt` covers this packet's files other than itself. Review output is machine-assisted; qualified native-speaker approval remains pending. No tests, builds, scans, CI dispatches, or workflow changes were run for this window.
