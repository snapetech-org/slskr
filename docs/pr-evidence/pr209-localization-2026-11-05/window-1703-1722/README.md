# slskR PR #209 localization review: W1703–W1722

## Pins and scope

This window contains 20 ordered source keys × 12 direct locales: 240 cells. Candidate-free, primary, blind, cross-review, and root adjudication are pinned to product head `91e109efba44ad9e53fe9544648a0d907a2bef77` / tree `38db78228144da5fc50179addccf826662bf97de`. The current catalog milestone is `0f05e049a241347d419c5705c0b8efc0c0030f76`.

The candidate-free input binds 30 caller references/occurrences across 17 files and has no callerless cells. It reattests prior applied/readback state at this head. All review packets and checksum manifests are copied in full below this directory.

## Adjudication

Primary review recorded 186 accepts, 19 corrections, and 35 refinements. The independent blind review recorded 195 accepts and 45 revisions. Cross-review accepted 170 current values, selected 25 corrections and 44 refinements, and held one cell. Root reviewed every cell and selected the cross-reviewed targets for the 69 changes; 170 current translations remain accepted. `1719::id` stays unchanged on hold because the proposals did not safely resolve the Indonesian rate-limit unit.

The main root choices correct count-label grammar, restore `Failover` as the technical concept, clarify fake-lossless warning scope, make seek buttons/tooltips describe the action, and align “Federated Taste” with its nested preference-recommendation panel. Federation rate-limit labels now identify permits and seconds consistently. `RustyMilk` remains byte-exact in every locale, ASCII `30` is preserved, and the ActivityPub `Pod` technical term remains intact.

The blind reviewer disclosed that, while locating the candidate-free directory, it saw primary-review filenames in the task-directory listing but did not open/read primary-review content or decisions before sealing. Its decisions were derived from candidate-free source/current/caller evidence only.

## Application and readback

`root-adjudication/apply_and_readback.py` verifies the pinned source/current hashes and every target, preflights all 12 catalogs, applies only the 69 exact-hash changes, and checks full-catalog readback. Verification passed for 240 reviewed cells, 5,441 keys per locale, unchanged key order and non-target values, and the retained hold.

No tests, builds, scans, CI, deployment, workflow edit, merge, release, or tag was made. This machine-assisted review does not establish qualified native-speaker approval or headed in-product browser acceptance.

## Evidence layout

- `candidate-free-input/` — pinned source, catalog, runtime, and caller evidence.
- `primary-review/` — primary decisions and verifier.
- `blind-review/` — sealed independent blind decisions.
- `cross-review/` — all-cell reconciliation, flags, and verifier.
- `root-adjudication/` — root ledger, exact-hash plan, apply/readback script, and final readback.
- `SHA256SUMS.txt` — checksum index for every evidence file in this window.
