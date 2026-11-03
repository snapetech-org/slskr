# slskR PR #204 W1223–W1242 third-party cross-audit

- Pinned PR head/tree: `1bb6a4c0d9ac2407ad3ab1191fe454d6661d4763` / `c92bb8f15ec61d538168b41859d9146bad91ae66`; PR #204 was open and draft at the pinned head during verification.
- Reconciled 240 cells: 142 accept-current, 47 corrections, 27 refinements, and 24 holds. Selected 216 targets and retained 24 no-caller holds.
- The source packet is candidate-free. The primary and independent blind ledgers and full packet are copied into this directory with their original checksum manifests.
- No repository files, tests, builds, scans, workflows, CI jobs, or PR actions were run or changed.

## Disposition counts

| Disposition | Cells |
|---|---:|
| accept-current | 142 |
| correction | 47 |
| hold | 24 |
| refinement | 27 |

## Reconciliation

- 142 current targets were accepted; the blind review independently marked those current targets as semantic pass.
- 74 targets changed: 47 corrections and 27 refinements. Of these, 46 current targets had a blind semantic/locale hold and 28 current targets passed the blind review; the blind review never saw the selected proposals. The cross-audit selected the primary proposal only after checking its exact meaning against caller/runtime context and confirming source tokens.
- All 24 cells for positions 1227 (“Download selected files”) and 1234 (“Downloaders”) remain held with no target because the pinned packet resolves zero exact caller references for either key.
- Caller references are exact source snapshots. Non-test-path references are not asserted to be production solely by path. The runtime lookup code maps exact source strings into locale catalogs.
- All selected targets pass the packet’s placeholder, markup, numeric-token, and protected-literal checks. Unit-bearing retry/retention candidates preserve milliseconds/minutes.
- The blind ledger assessed the current target only; it did not see or assess selected candidates. This cross-audit does not provide qualified native-speaker approval or release approval.

## Per-position counts

| Position | Source key | Accept current | Correction | Refinement | Hold |
|---:|---|---:|---:|---:|---:|
| 1223 | Download retry attempts | 2 | 9 | 1 | 0 |
| 1224 | Download retry delay milliseconds | 2 | 6 | 4 | 0 |
| 1225 | Download retry incomplete strategy | 0 | 9 | 3 | 0 |
| 1226 | Download retry max delay milliseconds | 2 | 7 | 3 | 0 |
| 1227 | Download selected files | 0 | 0 | 0 | 12 |
| 1228 | Download succeeded retention minutes | 0 | 9 | 3 | 0 |
| 1229 | Download the selected files from {folder}? | 12 | 0 | 0 | 0 |
| 1230 | DownloadFileComplete | 12 | 0 | 0 | 0 |
| 1231 | Downloaded | 11 | 1 | 0 | 0 |
| 1232 | Downloaded or prepared for import review. | 11 | 0 | 1 | 0 |
| 1233 | Downloaded · | 12 | 0 | 0 | 0 |
| 1234 | Downloaders | 0 | 0 | 0 | 12 |
| 1235 | Downloading | 12 | 0 | 0 | 0 |
| 1236 | Downloads | 11 | 0 | 1 | 0 |
| 1237 | Downloads Active | 6 | 0 | 6 | 0 |
| 1238 | Downloads Queued | 7 | 1 | 4 | 0 |
| 1239 | Downloads Total | 12 | 0 | 0 | 0 |
| 1240 | Downloads after approval | 12 | 0 | 0 | 0 |
| 1241 | Downloads unavailable | 12 | 0 | 0 | 0 |
| 1242 | Dropped Requests | 6 | 5 | 1 | 0 |

## Attestation

- Candidate-free input manifest SHA-256: `fddc720597ace3e2598efd690cd5b6e07a9fa23b9120e2513cab8a34cc1c9b95`.
- Primary ledger SHA-256: `84d0f1ff30e5b618ff6611da771a7a37c4d0934614ab2a06d9efbb8d01195038`.
- Independent blind ledger SHA-256: `9c6ae855a4727a67ca657c8463fc6b1272ff3a5fc36543a982e9b2c654c3c87d`.
- Exact pinned files: 36/36 caller/catalog/runtime file pins matched the commit; all 495 captured caller-context line hashes matched. All 240 source/current target hashes and current catalog lookups matched the pinned catalogs.
- Live GitHub PR head and commit tree matched the packet attestation; packet, primary, and blind checksum manifests verified.
- The selected target text is a review recommendation. No release is approved.
