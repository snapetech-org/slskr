# slskR PR #204 W963-W982 root-adjudication proposal

## Exact pin and coverage

- PR #204 is OPEN/DRAFT on `codex/slskr-l10n-audit-20261030`.
- Exact head: `99282b2f9b904f9814f5be66d8f643175e134f8e`; tree: `ba0ba0790da40159b8d92935f0866cb6a112edce`.
- The PR API, GitHub branch, and clean local worktree agree at this pin.
- Source positions 963-982 cover 20 sources and 240 populated cells in 12 locales.
- Source text, caller pins, current target text, and hashes agree for all 240 cells across the source-only input, primary ledger, blind cross-review ledger, and current catalogs.

## Recommended outcomes

- Accept current: 161
- Corrections: 22
- Refinements: 21
- Holds: 36

The 36 holds remain for all locales of positions 970, 971, and 980; no new exact production caller evidence resolves them. Position 964 gets corrected in all locales because the production component tracks locally disabled authority keys in browser state; “local” should modify the disable choice, not describe where an authority is located. Clarify the English source before applying these targets if possible.

This is a proposal for root decision only. It includes the exact primary and blind-cross-review readbacks, the source-only cell input, and one reconciled record per cell. Recommendations preserve exact placeholder, markup, and protected-literal structure. Native-speaker approval is not claimed.

No repository or PR changes were made. No tests, builds, scans, CI, browser, or workflow work was performed.
