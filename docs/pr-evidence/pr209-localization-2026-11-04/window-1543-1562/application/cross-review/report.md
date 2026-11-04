# slskR PR #209 W1543-W1562 cross-review

## Pin and scope

PR #209 remained OPEN and draft=true. Filtered live metadata reports head c15eddffec2c4c24cc091b2a6ebf0c43fa58ef1b on codex/slskr-l10n-audit-20261104-resync and base main at 1bbaec9fdc63a86de343e37e33bae70d44301a36. The branch ref and pull ref both resolve to c15eddffec2c4c24cc091b2a6ebf0c43fa58ef1b; the exact commit tree is 4259db991f25fbbd0200963769e62bb7e2150806. The PR body and description were not requested or read.

The review reconciles 240 cells: source positions 1543–1562 across the 12 pinned locales. Candidate-free, primary, and independent blind input seals and verifiers passed. All 21 caller references were rehashed against the exact source worktree; 21 literal occurrences across 10 caller files, with no callerless positions.

## Outcome

Cross-review disposition: 208 accept current, 27 correction proposals, and 5 holds.

All 21 primary proposals are supported. Seventeen use the primary wording unchanged; four consensus-recommendation wordings at position 1543 are adjusted to match the exact pinned translated panel heading.

The blind review has 20 finding records covering 22 cells. Eighteen finding cells support a correction proposal. Four remain on hold: Arabic member-affinity wording at 1549, Korean affinity terminology at 1549, and Simplified and Traditional Chinese membership statistics at 1550. The Korean issue also requires position 1548 to remain held so both paired messages can be reviewed together.

Six corrections are additional to the primary proposals: five last-seen message strings at 1547, aligned to each locale’s paired display wording, and Hindi opinion statistics at 1553, aligned to its paired phrase. All recommendations preserve placeholders and other protected tokens.

## Disagreements and holds

Primary and blind findings overlap on 12 cells; 9 cells have only a primary proposal, 10 have only a blind finding, and 209 have neither. The primary-only proposals are supported. Six blind-only cells receive explicit correction proposals; four blind-only cells remain held.

The Korean affinity finding is directionally right that the pair is inconsistent, but its proposed direction is unresolved: the paired errors split between 친화도 and 친밀도, while the pinned panel heading and score label use 친밀도. Cross-review holds both error cells rather than selecting a term without fluent review.

The Arabic affinity wording also varies across the paired errors and panel labels. Chinese membership-statistics wording clearly shifts to member relationships, but the exact membership or status term cannot be selected from caller context alone. Those cells remain text-free holds.

## Integrity and limits

Current targets and all selected correction targets preserve source placeholder sequence, markup, numeric tokens, and protected literals: zero mismatches. Caller file, line, context, and aggregate source-context hashes match the pinned checkout. The cross-review does not apply changes to catalogs or the PR.

The localization documentation says catalog translations still need fluent-speaker review. No native-speaker sign-off or browser review was performed; the proposed targets remain review recommendations.

The complete cell ledger is cross-review-ledger.jsonl; unresolved findings are in cross-findings.json. The verifier is verify_cross_review.py. Input checksum-list SHA-256 values: candidate-free dd128958855b904a900f3a7f160d7929de948afbc5b72eaccfe36ff3b1b92e24; primary b4d29848a1c96acc7625e5b2f4cdbd9f719b984de821ba06826887433b534c2b; blind 2587db3602c69ee821e797ec072af38224fda27a6165eabb74b5cae9e193f928.
