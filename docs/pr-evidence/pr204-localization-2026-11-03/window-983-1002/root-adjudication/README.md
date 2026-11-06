# slskR PR #204 root adjudication: W983–W1002

This packet resolves all 240 locale cells at exact PR head `09a614a66f1104fe530773fb17c79ed6338aed02` / tree `963f283311ae39dfa5fc289386d99dcc0dac2f90`. The live PR was re-queried and remains OPEN/draft; the remote pull ref matches. Both source packet checksum lists passed. I reattested the 12 locale catalogs, sorted source positions, 240 current values and hashes, 33 caller pins across 14 production files, and cited caller lines with `git show 09a614a66f1104fe530773fb17c79ed6338aed02:<path>`.

## Decisions

- 152 accept-current, 47 corrections, 24 holds, and 17 refinements.
- All 24 cells at positions 983–984 remain held because exact source-literal search found no production caller. Current values remain unapproved.
- The four position-994 Hindi, Japanese, Korean, and Brazilian Portuguese values preserve the exact `Pod` literal. The standalone catalog entry is `Pod` in all locales. Both Chinese targets retain a grammatical refinement while preserving `Pod`.
- `adjudication-differences.jsonl` resolves all 34 cells where primary and cross-review differed. `root-decisions.jsonl` records a final target/hash and disposition for each cell. `exact-hash-apply-plan.jsonl` contains 64 corrections/refinements with exact catalog-file and current/new target hashes. It is a plan only.

## Cross-review caveat

The independent cross-review was not strictly blind in process. After checksum verification, its reviewer opened the primary README and saw aggregate disposition counts and same-window summary claims, but not the per-cell primary ledger or proposals before sealing. This caveat is preserved in the manifest and summary.

`exact-head-reattestation.json` records zero source, current-target, locale-keyset, caller, and structural mismatches. This is machine-assisted review and does not claim native-speaker approval. No repository or PR changes, tests, builds, scans, CI, browser actions, workflow changes, or releases were performed. `SHA256SUMS.txt` checksums every report artifact except itself.
