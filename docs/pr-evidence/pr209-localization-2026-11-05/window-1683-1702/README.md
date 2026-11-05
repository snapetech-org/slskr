# slskR PR #209 localization review: W1683–W1702

## Exact pins and scope

This window covers 20 ordered source keys across all 12 direct locales: 240 cells. Candidate-free input, primary review, blind review, cross-review, and root adjudication are pinned to product head f04b7f965aef79552d65d40a2eeb550e5e3b9cfa / tree 85fe880023e55e055660fd17599c291edd24a1c6. The product catalog commit is 4e47285a4d3979e61918566ce86d10f57375622c / tree cc07313a7f4e6b00e60f6b4583c5dbce7f40edbe.

Candidate-free review binds 21 caller references across 13 files and confirms all 12 catalogs contain 5,441 keys. The 240-cell packets preserve current values, caller evidence, catalog hashes, and exact source pins.

## Review and root decisions

Primary and independent blind review were reconciled across all 240 cells. Root selected eight changes and accepted 232 existing values; there are no holds.

The selected changes correct backfill terminology in Spanish, Korean, and Vietnamese; restore Korean colons where caller code appends dynamic errors; use the conventional Traditional Chinese spelling 註冊; clarify German member affinities; and refine Traditional Chinese Pod Discovery wording. The German selection preserves {error}. The caller evidence for the Traditional Chinese discovery label is limited to a server error allowlist, so that refinement remains moderate confidence.

Placeholder order differences were checked against named runtime substitutions. All placeholders remain present exactly once; markup and numeric checks pass. Arabic plural branches retain all six forms.

## Application and readback

Product commit 4e47285a4d3979e61918566ce86d10f57375622c changes exactly eight values in five locale catalogs. The guarded application and full-catalog verifier pass: all 240 reviewed cells match the final ledger; all 232 accepted values remain unchanged; all 12 catalogs retain 5,441 keys and original order; and every value outside the eight selected keys is byte-identical to the pinned parent serialization.

The root-application directory includes the exact-hash plan, eight root decisions, full 240-cell final ledger and readback, plus a reproducible apply/readback script. The adjacent directories preserve the candidate-free, primary, blind, and cross-review packets and checksum indexes.

## Acceptance status

This is machine-assisted multilingual review at moderate confidence. It does not establish qualified native-speaker approval or exact-head headed-browser acceptance. No tests, builds, scans, CI, deployments, workflow changes, merges, releases, or tags were run or made.

