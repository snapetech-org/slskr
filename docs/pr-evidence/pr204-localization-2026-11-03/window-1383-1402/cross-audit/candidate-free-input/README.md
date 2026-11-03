# slskR PR #204 W1383-W1402 candidate-free exact-head input

Pinned to the open draft PR head/tree in PR-attestation.json. This packet contains the 5,441-key current source queue, exact production callers, current 12-locale catalog/runtime hashes, and 240 current target cells for 20 sources × 12 locales. No translation proposals or semantic decisions are included.

The queue matches the previous committed queue. Selected positions are 1383–1402; position 1382 is the previous boundary and 1403 is the next boundary. Caller scanning searched exact quoted literals in tracked production JS/TS under src/ and web/src/, excluding tests, catalogs, docs, fixtures, and Storybook. Caller contexts include source line and nearby context hashes, file hashes, and Git blob IDs.

All 35 existing holds are reattested against current targets: 23 earlier holds and 12 callerless cells from W1363–W1382. The 140 previously selected keys across seven windows still match their exact source queue positions. Callerless or ambiguous entries remain held.

Run python3 verify-candidate-free.py and sha256sum -c SHA256SUMS.txt from this directory.
