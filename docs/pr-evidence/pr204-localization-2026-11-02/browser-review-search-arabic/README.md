# Arabic search page review

- Browser: headed Chrome in the isolated Agentic VM, 1440 × 1000.
- Route: `/searches`, with Arabic selected through a temporary local review fixture and no saved login.
- Baseline PR head: `9d3aae249503d1732cc890a650052c85c57b2919`.
- Screenshot: `searches.png` (SHA-256 `d952ff5de748258020d8e2308952cec934ff0231c5462261325b4abff8737b3c`).

The rendered navigation, connection status, search labels, empty state, acquisition profile, and player controls use Arabic. Review found that the acquisition profile summary and connection-state label bypassed the locale lookup despite having catalog entries; both paths now use `LocalizedText`, which also provides language and direction metadata. New `Connecting`, `Connection Failed`, and `Reconnecting` catalog entries cover all twelve direct locales. Independent review accepted all 36 new catalog values after one Indonesian wording refinement; its ledger is in `../connection-state-review/`.

This review used a local preview with mock API responses and no connection to the live Soulseek service. It covers the Arabic search route and its empty state only; it does not establish server-backed workflow coverage, whole-application acceptance, other-locale quality, or native-speaker approval.
