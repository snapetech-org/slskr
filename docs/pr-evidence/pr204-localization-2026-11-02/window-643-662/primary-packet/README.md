# slskR PR #204 W643–662 primary semantic review

This packet covers source inventory positions 643–662 across all 12 direct locales: 240 catalog cells. The source window is frozen to the 5,437-key baseline inventory (`dd5959b45ec3a7002806b3b03a8d434cb791cc737d2afe1554d24351eac6f313`). The input PR head was `aa106d2505de8c9ace2d7d6dbf2af9777651947d`, tree `f99e717b4b77c8da098e7b8fc163926d4d32e926`.

## Results

- 98 cells are accepted as current.
- 118 cells have proposed corrections or refinements, with exact current and candidate hashes in `correction-candidates.jsonl` and `primary-review-ledger.jsonl`.
- Twelve `Circuit building failed` cells match exact previously accepted locale records and are preserved without reopening.
- Twelve `Cleanup Expired` cells are held. The pinned UI copy says expired memberships are cleaned, but the backend route calls `clear_pending()` on all pending join/leave requests without checking expiry. The source/action contract needs correction before a truthful localized label can be approved.
- The `Cleanup Seen Messages` caller/backend removes tracking records for messages marked seen; it does not remove message contents. Candidate wording names those tracking records. Its completion counters likewise count those records.
- All 240 current source/target placeholder checks and all candidate placeholder and markup checks pass. The candidate `Chromaprint`, `Pod`, and SQLite `VACUUM` protected-literal checks pass.
- The catalogs have four extra keys outside the frozen source inventory: `OK`, `Connecting`, `Connection Failed`, and `Reconnecting`. They are outside this window.
- No native-speaker approval is claimed. Candidate text is a primary machine-assisted review and needs independent cross-review/native-speaker review.

## Contents

`primary-review-ledger.jsonl` contains one row per cell. `correction-candidates.jsonl` includes each candidate with source/current/candidate hashes, placeholders, confidence, rationale, and caller pins. `held-cells.jsonl` records the behavior-mismatch hold. `source-inventory.jsonl`, `source-context.jsonl`, `current-cells.jsonl`, `caller-context-pins.jsonl`, `source-current-attestation.jsonl`, and `prior-evidence-matches.jsonl` preserve the frozen inputs and exact caller/source evidence. `primary-summary.json`, `primary-verification.json`, and `final-reattestation.json` summarize the review, structural checks, and exact-head reattestation.

The requested committed `window-623-642` directory was not present in the input PR tree; the W623–642 primary task-scratch packet was used to match its review schema. The repository worktree and PR were not modified. No tests, builds, scans, CI jobs, browser work, workflow edits, releases, tags, or merges were performed.
