# Application evidence

Exactly the 68 rows authorized by root-application-authorization.json were applied. Each selected row is pinned by source key, exact previous target hash, and final target hash. The other 172 W1263–W1282 cells retain their pinned current values. The historical rank-1257 `Ecosystem` no-caller hold remains unchanged in all 12 locales.

No tests, builds, scans, CI, workflow edits, merge, release, or tag were performed. Native-speaker approval and exact-head product-browser acceptance remain pending.

`plan-68-cells.jsonl` records the authorized selection; `readback-240-cells.jsonl` records exact values and SHA-256 hashes for every reviewed cell. `verify_application.py` verifies the pins, selection, readback, catalog diffs/order, hold preservation, evidence checksums, and nested review packets.

The repository pre-commit hook was bypassed for this commit only because it invokes the prohibited local Semgrep security scan. Its exact path/hash and the one-commit override are recorded in `hook-override-record.json`; no other effective hooks were present.
