# Primary semantic review summary — slskR PR #204 W1223–W1242

- Exact source pin: `1bb6a4c0d9ac2407ad3ab1191fe454d6661d4763` / tree `c92bb8f15ec61d538168b41859d9146bad91ae66`; PR branch and pull-ref were verified equal to this head in the sealed input packet.
- Reviewed **240 locale cells** across **20 source keys** and **12 runtime locales**.
- Decisions: **142 accept-current**, **47 correction**, **27 refinement**, **24 hold**.
- Confidence: {'high': 211, 'moderate': 29}.
- Caller-resolution holds: 24 cells across source positions 1227 (“Download selected files”) and 1234 (“Downloaders”), all 12 locales for each. No target recommendation is proposed for held cells because the sealed packet contains no exact quoted production caller for either key.
- Mechanical checks: placeholders 240/240 pass; markup 240/240 pass; numeric token sequences 240/240 pass; protected literals 240/240 pass. The `{folder}` placeholder, `DownloadFileComplete` event token, and `·` count separator are preserved. The milliseconds/minutes semantic-unit checks pass for all 36 recommended targets in the unit-bearing groups; 3 current targets omit a clear unit marker.

## Decision counts by source position

| Position | Source key | Accept | Correction | Refinement | Hold |
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

The complete per-cell ledger contains current and recommended target text, hashes, rationale, confidence, caller path/line references into the input packet, token checks, protected literals, and unit checks. Input manifest SHA-256: `fddc720597ace3e2598efd690cd5b6e07a9fa23b9120e2513cab8a34cc1c9b95`. Input `SHA256SUMS.txt` SHA-256: `352f2373e9b0fde26263b4802baf0ee1e8d8973d7705f21afd3041499778efb5`.

Caller evidence contains 55 exact source-key reference snapshots, including 11 references from explicitly test-named paths tagged test-only. Non-test-path references are not assumed to be production solely from their path. Caller holds still correspond to the two keys with zero exact references.
