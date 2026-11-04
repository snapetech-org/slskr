# slskR PR #204 W1463-W1482 candidate-free exact-head input

Pinned to the OPEN/DRAFT PR #204 head `2db7fa06845d9d94a5e5da2ddb5ecfdc04100ade` and tree `0945d38050243ed0d52aa9d923636820c66e65ba`. This packet contains current source queue, exact production caller context for the selected window, twelve locale catalog pins, all 240 current target cells for 20 sources × 12 locales, prior-selection reattestations, and carried-hold reattestations. It contains no proposed translations or semantic decisions.

The exact Unicode lexicographic source queue has 5441 keys and order SHA-256 `dcabd0a1f1e6e9504a47b5126d9f9fbd10aa5a2da80266ab945098248b97d983`; the current queue matches the prior W1443 candidate-free order. Selected positions are 1463–1482; the immediate previous boundary is position 1462 (`External Visualizer`) and the next boundary is position 1483 (`FTP username`). Prior selected IDs reattested: 220 across 11 candidate-free windows. Carried holds reattested: 35; unchanged 35.

Caller scanning searched exact quoted source-key literals in tracked production JavaScript/TypeScript under `src/` and `web/src/`, excluding tests, catalogs, docs, fixtures, and Storybook. It scanned 324 tracked production files and pinned each selected caller line/context with file and Git blob hashes. Callerless selected positions: 1466.

Baseline token checks over selected current cells: placeholder 0, markup 0, numeric 0, protected-literal 28 mismatches.

The candidate-free source, catalog, selection, hold, caller, and checksum verifier is `verify-candidate-free.py`. Run `python3 verify-candidate-free.py` and `sha256sum -c SHA256SUMS.txt` from this directory.
