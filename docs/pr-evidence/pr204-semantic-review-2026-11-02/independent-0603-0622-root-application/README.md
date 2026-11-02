# slskR PR #204 W603–622 exact-hash application

This batch reviews 20 source IDs × 12 direct locales (240 cells) at input head `f9a852b0f914b53510013dcedbeb3e332275b92d`, tree `bbbfde5fa90f60b656bc4d1a551afaf4cc645742`.

## Review and application

The primary review marked 177 cells accept-current, proposed 58 corrections and 5 refinements, and raised no holds. Independent cross-review accepted 232 cells, refined one primary proposal, and identified seven additional current issues. It accepted 62 of the 63 primary proposals. The final application changes 70 existing targets: 62 accepted primary proposals, one independently refined target, and seven missed issues. The other 170 cells remain unchanged.

The change set was applied only after exact source, current-target, proposed-target, catalog and caller pins matched the frozen review records. All 70 targets were read back and re-hashed. All twelve locale catalogs retain their 5,438 existing keys, with no additions or removals. Per-locale change counts and catalog hashes are in `apply-readback-report.json`.

The independent review re-attested 504 caller references across 42 unique caller path-and-line pins. Source, current-target, catalog-blob and caller-pin mismatch counts were zero; placeholder and protected-literal parity failures were zero. Each frozen primary and cross-review packet also passes its own checksum manifest.

## Scope and remaining review

A related Chinese `Full` preset label was flagged as a separate source row outside this batch; its exact caller and proposed wording are being recorded in a follow-up packet for the next sequential review. Qualified native-speaker approval remains outstanding; this machine-assisted review does not establish it.

Only the twelve locale catalogs changed. No source or workflow files changed. No tests, builds, scans, CI jobs, releases, tags or merges were run or created. PR #204 remains open and draft.

## Evidence files

- `primary/` — frozen 240-cell primary review packet.
- `crossreview/` — full independent 240-cell cross-review ledger and summary.
- `exact-hash-apply-plan.json` — the 70 accepted final targets with before/after hashes.
- `apply-readback-report.json` — exact base checks, locale counts, key parity and post-write hashes.
- `SHA256SUMS` — checksums for this evidence tree other than this manifest.
