# Connection-state localization review

The review is pinned to slskR PR #204 input head `9d3aae249503d1732cc890a650052c85c57b2919`. It covers `Connecting`, `Connection Failed`, and `Reconnecting` across all twelve direct locales: 36 target cells. Independent review accepted all 36 after one Indonesian refinement (`Menyambung kembali`), which is applied.

Both rendering paths now use `LocalizedText`: the server connection badge and the agent controller state. The acquisition profile summary also uses `LocalizedText`; all seven summary strings already exist in all twelve catalogs. The browser evidence for the Arabic search page is in `../browser-review-search-arabic/`.

The review ledger and summary are checksummed by `SHA256SUMS`. This is machine cross-review, not native-speaker approval.
