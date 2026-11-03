# slskR PR #204 W1403-W1422 candidate-free exact-head input

Pinned to the open draft PR head/tree in PR-attestation.json. This packet contains the 5,441-key current source queue, exact production callers, current 12-locale catalog/runtime hashes, and 240 current target cells for 20 sources × 12 locales. No translation proposals or semantic decisions are included.

The queue matches the previous committed queue. Selected positions are 1403–1422; position 1402 is the previous boundary and 1423 is the next boundary. Caller scanning searched exact quoted literals in tracked production JS/TS under src/ and web/src/, excluding tests, catalogs, docs, fixtures, and Storybook. Caller contexts include source line and nearby context hashes, file hashes, and Git blob IDs.

All 35 existing holds are reattested against current targets: 35 carried holds from W1383–W1402. The 160 previously selected keys across eight windows still match their exact source queue positions. Callerless or ambiguous entries remain held.

Run python3 verify-candidate-free.py and sha256sum -c SHA256SUMS.txt from this directory.
