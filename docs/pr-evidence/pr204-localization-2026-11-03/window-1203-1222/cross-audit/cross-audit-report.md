# Cross-audit report — slskR PR #204 W1203–W1222

## Pinned state and coverage

Live PR, branch, pull ref, and commit API agree on head `7c0dd5844d39e5fdb5269fa50317b26f117512a2`; tree `ba62eed0bd600a8f69bb6c0cbefe99da7ee47623`. PR is open and draft, based on `main` at `2a2b188f10b9460a15bc6d5c34e406b0193d51ba`. Reconciled 20 source keys × 12 locales = **240/240 cells**, plus all 86 caller references. The candidate-free input, primary ledger, and blind ledger checksum manifests pass.

## Reconciliation

Reviewers match on disposition and effective target for 176 cells. They differ on targets for 64 cells, with 11 disposition conflicts: 8 primary proposals where blind accepted current, and 3 primary accepts where blind proposed a change. The other 53 target differences are competing proposals.

Recommendation: **136 accept current, 80 correction/refinement proposals, 24 holds**. All holds are for every locale at positions 1206 “Download Clients” and 1216 “Download filters”; no exact caller was resolved. Among differing targets, the final value follows the primary in 36 and blind in 28. Cell-level decisions and rationale are in `cross-audit-decisions.jsonl`.

Primary-only changes judged justified include Arabic hamza spelling, Spanish and Vietnamese case/idiom improvements, Indonesian in-progress wording, selected-items explicitness in Arabic/Indonesian, and grammatical Hindi download-mode status. Blind-only changes judged justified include maximum-concurrent-downloads wording for “Download Slots” in all locales, explicit speed-limit phrasing for “Download KiB/s”, and Hindi selected-items and unset-path wording. Every recommendation retains exact `KiB/s`; five current translations omit it.

No unsupported caller claims or unsafe edits were identified. Source/current/proposal hashes, catalog pins, caller-context row hashes, placeholders, markup, and numeric-token checks reconcile. Caller wording supports the speed-limit, maximum-concurrent-downloads, retention-duration, leaderboard, and missing-path meanings recorded in the ledger.

## Limits

This is a machine cross-review, not native-speaker approval. Some choices between equivalent locale variants remain language-quality judgments and merit native-speaker confirmation. No repository/PR edits, tests, builds, or CI were run.
