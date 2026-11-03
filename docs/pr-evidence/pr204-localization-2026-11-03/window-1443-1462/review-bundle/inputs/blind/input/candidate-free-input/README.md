# slskR PR #204 W1443-W1462 candidate-free exact-head input

Pinned to the OPEN/DRAFT PR head and tree in PR-attestation.json. This packet contains the current 5,441-key source queue, exact production callers, twelve locale catalog/runtime hashes, and 240 current target cells for 20 sources by 12 locales. It includes no proposed translations or semantic decisions.

Selected positions are 1443-1462; position 1442 is the previous boundary and 1463 is the next boundary. Caller scanning searched exact quoted literals in tracked production JS/TS under src/ and web/src/, excluding tests, catalogs, docs, fixtures, and Storybook. Caller contexts include source line and nearby context hashes, file hashes, and Git blob IDs.

All 35 carried holds are reattested against current targets. The 200 previously selected source keys across ten windows still match their exact source queue positions. Callerless or ambiguous entries remain held.

Run python3 verify-candidate-free.py and sha256sum -c SHA256SUMS.txt from this directory.
