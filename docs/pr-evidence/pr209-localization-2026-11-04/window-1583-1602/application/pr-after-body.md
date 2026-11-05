# slskR localization audit and translation follow-up

This draft replaces [PR #204](https://github.com/snapetech-org/slskr/pull/204) so the already-pushed localization changes are attached to a pull-request head that matches its branch. On 2026-11-04, the PR API and refs/pull/204/head remained at f6fbf614e7e2ff869e4ca86ae96103cff604b79c while the same-repository branch contained two additional, ordinary commits through c15eddffec2c4c24cc091b2a6ebf0c43fa58ef1b. The new branch points at that existing commit. No history was rewritten and no commit was amended or copied. The old PR is closed after this replacement is verified; its complete historical review narrative remains available there.

## Localization scope

The audit covers all 12 direct target locales: Spanish, Simplified Chinese, Hindi, German, Japanese, French, Brazilian Portuguese, Arabic, Korean, Traditional Chinese, Vietnamese, and Indonesian. English remains the fallback. Every locale catalog retains the same ordered set of 5,441 keys.

The preceding audit windows, reviews, and readbacks are preserved in the history and evidence linked from PR #204. This replacement carries all existing product and evidence commits plus the current W1523–W1542 follow-up.

## W1523–W1542 review and application

The primary, independent blind, and cross-review packets cover 240 cells across 20 source positions and 12 locales. Cross-review selected 8 target updates, retained 222 current values, and placed 10 cells on hash-only hold where caller context does not resolve whether “backfill” means retroactive loading, completion, or synchronizing missed messages. The approved changes affect the German, French, Hindi, Korean, and Vietnamese catalogs. Readback preserves every other target and all ordered catalog keys.

- Product commit: 09497027d7ca64892cf8ce3530dd5cc1fdf93c15
- Evidence commit / PR head: c15eddffec2c4c24cc091b2a6ebf0c43fa58ef1b
- [Complete review, application, and readback evidence](https://github.com/snapetech-org/slskr/tree/c15eddffec2c4c24cc091b2a6ebf0c43fa58ef1b/docs/pr-evidence/pr204-semantic-review-2026-11-04/independent-1523-1542-root-application/)

## Review and validation limits

This is machine semantic review. Qualified native-speaker approval and exact-head headed-browser acceptance are not claimed. No tests, builds, scans, CI dispatches, workflow edits, merges, releases, or tags were made. The existing .github/workflows files are unchanged.

## W1543–W1562 localization application (2026-11-04)

Applied 27 cross-reviewed corrections in product commit 9f158221682915a9c6c238c5e182871adbf93efd across 11 locale catalogs. Exact readback covered all 240 cells: 208 accepted values and five held values were retained unchanged. All 12 catalogs retain 5,441 keys and their original key order.

The five holds remain unchanged for fluent-speaker review: Arabic member-affinity wording at 1549, Korean affinity wording at 1548–1549, and Simplified and Traditional Chinese membership statistics at 1550. The review and application have no native-speaker sign-off or browser review. No tests, builds, scans, or CI were run. Application evidence: docs/pr-evidence/pr209-localization-2026-11-04/window-1543-1562/application/

## W1563–W1582 localization application (2026-11-04)

Applied 18 reviewed catalog updates (16 corrections and 2 refinements) across all 12 locale catalogs in product commit `62e74939e7b8145055dbd77d83d2b5c3804d3b0b`. The W1569 Hindi, W1570 Hindi, and W1570 Spanish values use the separate root adjudications. The other 222 cross-review accept-current values retain their exact hashes; there were no holds.

All 12 locale catalogs retain 5,441 keys and their original order. The application evidence includes exact copies of the candidate-free, primary, independent blind, and cross-review packets, plus the separate root adjudication supplement: `docs/pr-evidence/pr209-localization-2026-11-04/window-1563-1582/application/`.

No tests, builds, scans, CI, workflow edits, merge, release, or tag were performed. No native-speaker sign-off or browser review was performed.

### W1583–W1602 — fixed server errors

Reviewed all 240 catalog cells for 20 source messages across 12 locales, including their production callers. Applied four approved changes in product commit `dab83932bb2b375caf3f588ac7b20b3bd835a419`: two corrections and two refinements across the Brazilian Portuguese, Traditional Chinese, and Vietnamese catalogs. The remaining 236 cells were retained unchanged; all 62 carried prior holds were reattested unchanged, with no new holds.

The primary review, independent blind review, cross-review, and root adjudication are recorded in the PR evidence. The blind reviewer disclosed one generic public search about Traditional Chinese wording; the cross-reviewer did not access or rely on it. Native-speaker signoff and headed browser review remain outstanding. No tests, builds, scans, CI, or workflow edits were performed.
