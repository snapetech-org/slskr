# slskR PR #204 W723–742 primary review

- Exact live PR head/tree: 32903976fabe543f89dd5950245ba11dd77c8eb3 / ebf75888b3087e83fe2327495c17611802925f71 (OPEN, DRAFT).
- Reviewed zero-based source positions 723–742: 20 source IDs × 12 locales = 240 cells.
- Primary decisions: 150 accept-current, 41 correction proposals, 49 holds.
- Holds: 36 cells across three strings with no pinned direct caller; 12 cells for the messaging-panel string whose “leaving anything” wording is ambiguous despite a direct caller; one Vietnamese diagnostic-bundle term hold.
- The messaging caller only removes the panel from local UI state. Clarify the source copy about room/channel membership before translating it.
- Reattested W722 (Close) at the immediate preceding inventory index: all 12 prior proposed targets are present at this head and all 11 prior caller-pin rows match live line hashes and file blobs. W723 is Close browse tab {label}.
- The frozen inventory has 5,437 source keys. Each live locale catalog has seven keys outside it and four frozen keys absent; see manifest.json for exact deltas. The new username-interpolated loading message is outside this window.
- All 41 proposals preserve exact source placeholders and protected literals (Soulseek, ListenBrainz, CSV). Qualified native-speaker review remains required; no native-speaker approval is asserted.
- No repository or PR changes, tests, builds, scans, CI, workflows, browser review, releases, tags, or merges.
