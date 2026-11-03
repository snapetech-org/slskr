# Primary semantic review — slskR PR #204 W1243–W1262

Pinned to exact open draft PR head `ce2e7d12f3025f0312df37527b4c270d0eb5bce5` / tree `0ead1eb1678b4df05ca7feec9776c0319d4eefd3`. The candidate-free input at `/mnt/disks/scratch/task-scratch/slskr-pr204-w1243-1262-input-20261103/clean-input` was checksum-verified and re-attested against the PR branch and `refs/pull/204/head` before review. No other review candidate or blind/cross-audit output was used.

The ledger covers all 240 cells (20 source keys × 12 locales). It records current and recommended targets, disposition, rationale, confidence, caller-line hashes, placeholders, markup, numeric and protected-literal checks, plus unit checks for seconds and minutes. All 12 cells for position 1257 (`Ecosystem`) are held because no exact caller is pinned; this is a caller-resolution hold, not a locale-quality judgment.

The four server validation messages at positions 1252–1254 and 1256 append API field names absent from their English source strings. The primary recommendation removes those implementation details while preserving each translated validation sentence and technical `ContentID` literal. Position 1255 has no such suffix and is accepted in all locales. The `Edges` label at position 1258 is reviewed in its graph-atlas caller context.

This machine-assisted primary review does not establish qualified native-speaker approval. A separate blind review and cross-audit are not included here. No repository or PR changes, tests, builds, scans, or CI were performed.
