# slskR selected transfer actions and W563–582 follow-up

Applied to PR #204 from reviewed input head `aa106d2505de8c9ace2d7d6dbf2af9777651947d` (tree `f99e717b4b77c8da098e7b8fc163926d4d32e926`).

- Added the independently cross-reviewed `Retry selected` and `Cancel selected` translations for all 12 direct locales. `TransferGroup.jsx` uses complete localized IDs for multi-selection and retains existing single-action IDs for one selected item.
- Removed the unused `Retry{all}` and `Cancel{all}` catalog keys after replacing their callers. Each locale catalog keeps its prior key count.
- Kept `Remove{all}` and its caller pending a behavior decision. The browser callback sends `remove=true`; the active server route treats that as a local-file deletion request even when the caller passes `deleteFile=false`. The adjacent action also advertises disk deletion. The proposed `Remove selected` translations remain held.
- Applied five reviewed W563–582 wording corrections: Japanese `Cancelled`, Japanese and Korean `Canonical support from`, and the Simplified and Traditional Chinese RustyMilk FPS tooltip.

`apply-plan.jsonl` records exact source and target hashes. `readback.jsonl` records post-edit values and retired keys. Original packets and checksum manifests are preserved in `primary-transfergroup/`, `independent-transfergroup-cross-review/`, `window-563-582-reconciliation/`, and `window-563-582-live-readback/`. No tests, builds, scans, CI, workflow changes, releases, tags, or merges were performed. Native-speaker approval and headed-browser review at this follow-up head are not established.
