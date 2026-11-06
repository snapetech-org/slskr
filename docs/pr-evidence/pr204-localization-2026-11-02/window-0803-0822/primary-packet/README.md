# slskR PR #204 W803–W822 primary semantic review

- Live PR state at freeze: OPEN/DRAFT, branch codex/slskr-l10n-audit-20261030, head 3a4c26a7faf1dacbd8f3a382d47243b7063a262d, tree 9059d27001d306ea6b064560137ff2a51dd19021.
- Reviewed 20 source keys at current sorted-inventory zero-based indices 802–821, labeled W803–W822; 12 direct locales, 240 cells.
- Inventory is the lexically sorted exact key set, not JSON insertion order. All 12 catalogs contain the same 5,440 keys; see catalog-and-inventory-attestation.json.
- W783–W802 reattest at indices 782–801; W803 starts at 802. W822 ends at 821; W823 is index 822.
- No prior source-window cell-review dispositions were found in tracked PR evidence. All 240 cells were reviewed fresh; no prior disposition was reused.
- Exact caller paths, lines, hashes, Git blob IDs, and nearby code are in caller-context-pins.jsonl; per-source summaries are in source-context.jsonl.
- Exact source and target hashes, current values, candidates, placeholders, selectors, markup, protected literals, and decisions are in primary-review-ledger.jsonl; proposals only are in correction-candidates.jsonl.
- There are zero ICU selectors. W817 has the sole placeholder {urlBase}, preserved by all current and proposed targets. No markup tokens occur. ListenBrainz, API, and URL preserve case.
- W816 Configured has one caller gap: LidarrPanel.jsx lines 44 and 109 renders the raw English status instead of localizing it.
- Decisions: {"accept-current": 134, "propose-correction": 80, "propose-refinement": 26}; candidates: 106; cell holds: 0.
- Moderate-confidence machine semantic review; native-speaker approval remains outstanding.
- Read-only: no repository or PR writes, tests, builds, scans, CI, browser/workflow, release, tag, or merge actions.
