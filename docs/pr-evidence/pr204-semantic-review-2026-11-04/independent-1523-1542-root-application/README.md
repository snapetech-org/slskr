# slskR PR #204 W1523–W1542 cross-review application

This evidence records application of the sealed cross-review at input head `f6fbf614e7e2ff869e4ca86ae96103cff604b79c`, tree `536b0fc02a3c16fa7eb0f9d5504a4c8c91b2152d`.

The product commit changes exactly eight selected targets in five locale catalogs. The other 222 cells remain current. The ten backfill cells at positions 1538–1539 for es, pt-BR, ar, vi, and id remain unchanged and are recorded hash-only. All twelve catalog files matched their pinned base hashes before editing; all 240 reviewed targets were read back, and catalog key sets remain unchanged.

`crossreview/` contains the complete portable review packet, including candidate-free input, primary and blind packets, cross ledger, rationale, prior hash-only lineage, verifier, and checksums. `exact-hash-apply-plan.json` records the eight selected changes; `apply-readback-cells.jsonl` records the 240-cell post-application readback.

Run `python3 verify-application.py` from this directory to verify the nested cross-review packet, evidence checksums, base and post-application values, key-set parity, and product commit scope.

The product/catalog changes are committed separately from this evidence. No tests, builds, scans, CI jobs, workflow edits, merge/release/tag, browser review, or native-speaker signoff were performed.
