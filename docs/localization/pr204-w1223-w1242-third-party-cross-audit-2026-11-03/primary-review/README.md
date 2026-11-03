# Primary semantic review — slskR PR #204 W1223–W1242

This is the primary semantic review paired with candidate-free input packet `/mnt/disks/scratch/task-scratch/slskr-pr204-w1223-1242-input-20261103`. It is pinned to head `1bb6a4c0d9ac2407ad3ab1191fe454d6661d4763` / tree `c92bb8f15ec61d538168b41859d9146bad91ae66`. The packet was checksum-verified before review; no blind review or cross-audit output and no PR body were read.

## Files

- `ledger.jsonl`: 240 per-cell decisions with exact current/recommended targets and SHA-256 values, rationale, confidence, caller references, placeholder/markup/numeric/protected-literal checks, and semantic unit checks.
- `summary.md`: scope, counts, caller holds, and mechanical checks.
- `SHA256SUMS.txt`: hashes for the report files.

Caller-resolution holds remain at positions 1227 (`Download selected files`) and 1234 (`Downloaders`), 12 locales each. All other cells have a complete target recommendation. No repository or PR was changed and no tests/builds/CI were run.

Caller evidence in the ledger mirrors the packet scopes: references from explicitly test-named paths are tagged test-only. The two held keys have no exact references of either scope.
