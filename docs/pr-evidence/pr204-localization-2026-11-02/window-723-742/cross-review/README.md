# slskR PR #204 W723–742 independent cross-review

- Exact live PR pin: OPEN/DRAFT at `32903976fabe543f89dd5950245ba11dd77c8eb3` / tree `ebf75888b3087e83fe2327495c17611802925f71`, rechecked before and after review.
- Scope: 20 source strings × 12 locales = 240 independently judged cells.
- The exact primary packet was copied to `primary-packet/`; its checksum manifest passes. The source inventory, 12 locale catalogs, all current cells, 49 caller pins across 13 files, and adjacent W722 boundary were reattested against the live tree.

## Review results

- 145 cells: accept current.
- 40 primary candidate targets: accept.
- 1 primary candidate target revised: W730 Vietnamese now uses the pinned `Wishlist` translation `Danh sách yêu thích`.
- 5 additional findings: W729 Japanese compound spacing; W730 Arabic, Hindi, Indonesian, and Simplified Chinese alignment with each catalog’s exact `Wishlist` term.
- Final ledger counts: 43 corrections, 3 refinements, 49 holds.
- Holds retained: 36 cells in W733/W740/W742 have no direct caller; all 12 W741 cells remain held because “leaving anything” does not describe the pinned local-state-only panel close; W724 Vietnamese remains held for fluent terminology review.
- W741’s close handler only filters the panel from local UI state. It does not delete a thread or leave a room/channel.
- W722 is adjacent and non-overlapping. Its 12 prior decisions and current targets remain present; all 11 prior caller pins still match. `prior-w722-context.jsonl` carries the exact row and caller-pin evidence.
- Placeholder, markup, and protected-literal mismatches in final targets: zero.

Confidence is moderate. Native-speaker approval remains outstanding. No repository/PR edits, tests, builds, CI, or browser actions were performed.
