# slskR PR #209 localization window W1603–W1622

This packet reviews the 20 selected source keys and all 12 direct locales at product head eeb63f1e4e21d801f4a4e0393813b6e86a1ff7c8 (tree 590ee410666905f68f601393b64a4798b0609181).

## Review

- Candidate-free input: 20 caller-backed source keys, 240 locale cells, exact source/caller/catalog hashes, and prior applied/hold reattestation.
- Primary review: 236 accept-current, 2 corrections, 2 refinements.
- Independent blind review: 227 accept-current, 13 corrections.
- Root cross-review: 227 accept-current, 11 corrections, 2 refinements. All 240 cells reviewed and 13 proposals resolved.
- Independent cross-review: 227 accept-current, 11 corrections, 2 refinements; zero disagreements with root.
- Placeholder, markup, numeric-token, and protected-literal checks passed.

## Application

Product commit bdc831fcde86101cd949fe70bd99acd8871ace4a (tree c9d994368a90e82f310a3c81a6ba059567c0e3bd) applies 13 reviewed values across eight locale catalogs. The application readback covers all 240 cells; catalog key sets and order are preserved, and all non-target values are unchanged.

The application verifier is application/verify-application.py. Run it with --repo pointing to a checkout that contains the recorded commits. Review packets and application files each include SHA256SUMS.txt files.

## Review limits

No exact-head deployment was available for headed browser review. Qualified native-speaker approval is not claimed. No tests, builds, scans, CI dispatches, workflow edits, merge, release, or tag were performed.
