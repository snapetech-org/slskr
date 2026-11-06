# slskR PR #209 W1643-W1662 primary semantic review

This packet is an independent primary semantic review of the 240 candidate-free cells at PR head `2d804c49879372071adf606bc2a2cf51e261fd94` (tree `d6f5552d2400d868c2f2af98eb68caadfd4f3f66`). It reviewed all 20 source keys in all 12 locales against the exact caller contexts and current catalog targets in the sealed candidate-free input. It contains no blind or cross-review material.

## Results

- 240 cells reviewed: 236 accept-current and 4 proposed corrections.
- Four proposals: 1643/ko, 1646/zh-Hant, 1649/hi, and 1654/zh-Hant.
- 0 callerless rows; the hash-only hold ledger is empty.
- Placeholder, markup, numeric-token, and protected-literal mismatches: 0. Proposed targets also preserve each source token signature.
- Prior continuity is reattested by the candidate-free packet: 400 prior selections, 2,160 prior window hashes, 62 unchanged holds, and 95 applied-target hashes. W1623-W1642 readback is pinned at 13 applied and 227 retained cells.

`primary-ledger.jsonl` contains every reviewed cell and binds its source, current target, caller evidence, locale catalog pin, decision, rationale, confidence, and token checks by hash. `proposals.jsonl` contains the four exact recommended target strings and their rationale. `holds-hash-only.jsonl` is empty because every row has a resolved production caller.

## Verification

Run `python3 verify_primary.py` from this directory. The default candidate-free input and exact-head worktree are the sibling `candidate-free-input/` and `worktree/` directories. Alternate paths can be provided with `--input` and `--worktree`. The verifier checks packet checksums, candidate-free seals, complete row coverage, source/current/caller hash bindings, proposal semantics and token preservation, and local Git head/tree/clean status. Live PR/branch/pull-ref snapshots taken before and after review are retained under `attestation/`.

## Limits

Overall confidence is **moderate**. Proposed corrections have per-row confidence in the ledger. No native-speaker or browser/UI signoff was obtained. No tests, builds, scans, CI, workflows, repository edits, or PR changes were performed.
