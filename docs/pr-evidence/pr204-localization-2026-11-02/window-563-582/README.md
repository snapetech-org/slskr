# slskR localization review W563–582

This exact-head window reviews 240 populated cells for source positions 563–582 across the 12 direct locales. It pins PR #204 input head `7e99edecbdea10580cc5e8d198930a82f076b834` and tree `55de069f88c197ab8ddd3c773c1f10e5cb86abd5`. Primary and independent review packets retain their original checksums below.

## Reconciled result

- Independent cross-review raw dispositions: 68 accepted, 6 refined, 2 missed, 12 held, and 152 no-op/keep rows.
- The root diff audit caught two target-field contamination errors in the Arabic and Hindi `Candidates` rows: both primary and cross-review entries contained reviewer explanations instead of localized labels. Root adjudication replaced them with `عناصر مرشحة` and `सुझाए गए आइटम`, based on the pinned caller showing a count of track recommendation items, not applicants. See `root-adjudication.jsonl`.
- Applied: 76 exact-hash changes across the 12 locale catalogs — 66 accepted primary values, 6 cross-review refinements, 2 missed corrections, and 2 root overrides.
- Held: all 12 `Cancel{all}` cells because the caller appends the English word `Selected`; changing only the catalog entry would leave mixed-language UI.
- The other refined and missed rows were checked against their pinned caller contexts: canonical-match support, canonical-recording variants, RustyMilk frame-rate wording, and Spanish/German candidate verdict labels.
- `apply-plan.jsonl` records each source, locale, caller, old/new text and hashes, and final adjudication. `readback.jsonl` contains post-edit exact-text and hash confirmation. Catalog key sets were preserved at 5,437 keys per locale.

The raw primary and cross-review proposal ledgers remain unchanged for traceability; root adjudication is the final authority for the two contaminated values. No qualified native-speaker approval or exact-head headed-browser review is established. No tests, builds, scans, CI, workflow edits, releases, tags, or merges were performed.
