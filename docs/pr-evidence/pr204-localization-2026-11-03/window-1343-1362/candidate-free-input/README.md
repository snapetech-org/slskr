# slskR PR #204 W1343-W1362 candidate-free input

Pinned to the live open draft PR commit/tree in PR-attestation.json. This packet contains source keys, exact production caller context, runtime and locale metadata, catalog pins, prior-hold reattestations, and all 240 current target values. It contains no translation proposals.

The source queue contains 5,441 unique English source keys sorted lexicographically by exact Unicode string. W1323-W1342 ends at position 1342; position 1343 is the first selected source in this packet. Position 1363 is the next boundary.

Caller scanning searched exact quoted source-key literals in tracked production JavaScript/TypeScript under src/ and web/src/. Tests, fixtures, Storybook, catalogs, and documentation were excluded. Caller excerpts include +/-4 lines and file/blob/line/context hashes. Catalog values, ordered keys, and runtime localization behavior are pinned to the same commit.

All 22 carry-forward holds from the preceding candidate-free packet and the W1323-W1342 Vietnamese federation hold were re-read at this head. Run python3 verify-candidate-free.py, then sha256sum -c SHA256SUMS.txt.
