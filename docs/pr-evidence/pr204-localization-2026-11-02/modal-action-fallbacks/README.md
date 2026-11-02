# Localize shared Modal action and Confirm fallback labels

At PR #204 input head `e4908e742db9f31a84c6aaaad43f4427c2db649b` / tree `93843e9d75c9d6846140346e80567be989d832af`, five plain `Cancel` actions in AppHeaderMenu, Files Explorer, and System Info reached the shared Modal string-action renderer, which rendered them directly. The generic Confirm component also used untranslated `Cancel` and `OK` fallback labels; `OK` was absent from the 12 locale catalogs.

The shared renderer now uses `interfaceText` and localized text attributes for string actions. Confirm now localizes fallback and explicit string labels and subscribes to interface-locale changes. The 12 direct catalogs each gained a localized `OK` button label, with identical 5,438-key order. `source-audit.json` pins the old caller lines and shared component blob; `catalog-apply.jsonl` and `readback.jsonl` record exact targets and hashes.

The added labels are machine-reviewed drafts; native-speaker review and exact-head browser review remain outstanding. No tests, builds, scans, CI, workflow changes, merges, releases, or tags were run.
