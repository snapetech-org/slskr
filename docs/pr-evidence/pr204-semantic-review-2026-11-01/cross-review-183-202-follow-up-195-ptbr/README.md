# Parent cross-review and focused pt-BR follow-up

The parent independently reviewed the exact 44-cell application from source indices 183–202 against PR head `6a8415d2df2f22935188992e03c4636052de2d67` / tree `f562ac9ed6108921efbef4272973b8895bb4c22a`. The original root ledger is retained byte-for-byte in `parent-cross-review-44.jsonl` (SHA-256 `540ae4de10b019726dee36779d802115bf102b5a35cec77b71eb74b876ce045b`): 43 rows are accepted as applied and one row is refined-and-accepted; there are no holds. The original 44-row application evidence remains unchanged in `independent-0183-0202-all-12-locales/applied-corrections.jsonl` (SHA-256 `ac21337cd22ccff47d23cb724c3fb4a7009e330144ef4697aa3a4d3cd2f05b8a`).

The refined row is source index 195, locale `pt-BR`, source `Added {interest} as a hated interest.`. The exact previous applied target at the cross-review head was `{interest} foi adicionado à lista de interesses indesejados.` (SHA-256 `2de4ba4e3eee3f3e7e6d347c28c9a59622453bb5743c6c9580665748edee4c70`). It was changed in the separate focused catalog commit `44333cff18f24d67e5552e3289980beca8aa996d` / tree `4a2886515367cd8fd1acd03fb6f3eb175d1f8500`, parent `cea88305885c27879ecd1569944ee86bdf78e2b2`, to `O interesse “{interest}” foi adicionado à lista de interesses indesejados.` (SHA-256 `5a2b2a88b47a122b2c2a5725eaa53729d2e34f12b3468be573c71bfd11b9505f`). The explicit noun controls Portuguese gender agreement independently of the interpolated placeholder.

`refinement.jsonl` records the exact source/old/new hashes, cross-review ledger checksum, and application commit pins. `verify_followup.py` checks all 44 cross-review rows, the original application cell at `cc55673`, the one-cell refinement diff, current catalog value, placeholder, and bundle checksums. The original 183–202 batch verifier also checks this explicit post-application override while preserving the historical 44-row evidence.

Native-speaker approval remains outstanding. No release or tag was made.

Run from the PR worktree:

```sh
python3 docs/pr-evidence/pr204-semantic-review-2026-11-01/cross-review-183-202-follow-up-195-ptbr/verify_followup.py --repo "$PWD"
```
