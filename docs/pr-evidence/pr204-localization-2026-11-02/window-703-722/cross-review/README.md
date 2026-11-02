# slskR PR #204 W703–722 independent cross-review

Read-only, cell-by-cell cross-review of the pinned primary packet.

## Pin and evidence

- PR #204 is OPEN/DRAFT at `8b2f1f5fb216fb9946e823c5dff86d5e76a30b84`; exact tree `90225bd501256ac84c520105e714df9fc9d6aefc`.
- Reattested 12 current catalog blobs, 20 source inventory rows, all 240 current locale cells, and all 36 caller lines at the exact current head. The 36 pins cover 28 caller files.
- Compared current catalogs with W563 head `7e99edecbdea10580cc5e8d198930a82f076b834` to account for intervening PR updates. None of the 20 W703–722 keys changed between those catalog snapshots; all 240 current cells were still re-read and hash-verified at the current head. Eighty changed source keys fall in W563–702; out-of-window deltas (`Full` at position 1823, `Retry{all}` at position 3621, and other catalog-only additions/removals) are recorded in `catalog-history-summary.json` but not semantically reviewed here.
- One of 28 caller files changed since W563: `web/src/semantic-ui-react/index.jsx`, in the shared modal/action localization follow-up. Current W722 call sites were independently pinned at the current head.

## Findings

- `cross-review-ledger.jsonl` and `final-targets.jsonl` contain an independent disposition and exact final target for all 240 cells. `candidate-assessments.jsonl` assesses all 67 primary proposals.
- 63 primary candidates are confirmed exactly; 2 proposals duplicate the current Korean values and are retained as no-ops; 2 are refined for French semicolon spacing and Korean punctuation. Eight additional clipboard-instruction corrections are recorded for Arabic, Spanish, Japanese, and Korean.
- The Arabic `Cleared {count} searches` value remains a structured six-category ICU map (`zero`, `one`, `two`, `few`, `many`, `other`). Every branch retains `{count}`. Keep it on hold pending qualified Arabic review of noun forms.
- All 12 `Click to load native Soulseek interests for` cells remain held. `UserCard.jsx:336` concatenates a literal space, username, and period after the localized fragment. `LocalizedText` accepts `values` and passes them to `t`; change the source to `Click to load native Soulseek interests for {username}.` and pass `values={{ username }}` so each locale can order the complete sentence. Catalog-only changes cannot fix the fragment.
- The 12 previously accepted `Circuit building failed` decisions remain unchanged and their exact target hashes still match at the current head. They are out of this window and were not reopened.

## Files

- `cross-review-ledger.jsonl`: 240 dispositions, exact final targets/hashes, placeholder/markup/protected-literal checks, pinned caller context, and rationale.
- `candidate-assessments.jsonl`: all 67 primary proposed targets and independent outcomes.
- `final-targets.jsonl`: compact final target list.
- `hold-groups.json`: ICU plural review and username interpolation source refactor.
- `caller-reattestation.jsonl`, `source-row-reattestation.jsonl`, and `prior-accepted-circuit-building-preservation.jsonl`: exact pin evidence.
- `inputs/`, `primary-input/`, and `primary-*.jsonl`: raw snapshots and frozen primary context.
- `SHA256SUMS`: checksums for every packet file.

Native-speaker approval remains outstanding. No repository or PR files were changed; no tests, builds, scans, CI, browser review, workflows, releases, tags, or merges were run.
