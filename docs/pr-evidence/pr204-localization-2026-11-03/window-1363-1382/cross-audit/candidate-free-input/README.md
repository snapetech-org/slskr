# slskR PR #204 W1363-W1382 candidate-free exact-head input

This candidate-free packet is pinned to live open draft PR #204 at the exact head/tree in PR-attestation.json. It contains the current source queue, production caller context, runtime/catalog pins, all 240 current target cells for 20 sources × 12 locales, prior-selection reattestations, and 23 carry-forward hold reattestations. It contains no translation proposals or semantic decisions.

The source queue is the exact Unicode lexicographic order of 5,441 unique keys shared by the 12 locale catalogs. The committed W1343-W1362 queue and all six prior candidate-free selections listed in source-order-lineage.json were re-read and matched against this exact-head queue. The selected ranks are 1363-1382; the immediate previous boundary is position 1362 (Enforce) and the next boundary is position 1383 (Entries:).

Caller scanning searched exact quoted source-key string literals with quote, backslash, and common newline escapes accounted for in tracked production JavaScript/TypeScript under src/ and web/src/, excluding tests, catalogs, docs, fixtures, and Storybook paths. Each caller excerpt includes file/blob/line/context hashes. Current catalog targets, locale order, and runtime placeholder behavior are pinned at this exact head.

prior-hold-reattestation.jsonl carries forward all 23 existing holds from committed W1343-W1362 evidence. Each current target was re-read from the exact-head locale catalog; rows record whether the target is unchanged. These attestations do not extend the selected window.

Run `python3 verify-candidate-free.py` and `sha256sum -c SHA256SUMS.txt` from this directory.
