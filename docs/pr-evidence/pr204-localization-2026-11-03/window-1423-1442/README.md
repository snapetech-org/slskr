# slskR PR #204 localization review and application — W1423–W1442

This portable packet contains the candidate-free input, primary review, independent blind review, third-party cross-audit, and exact-head application evidence for 20 source strings across 12 locales (240 cells).

The reconciled result is **201 accept-current, 38 corrections, 1 refinement, and no new holds**. The application updates exactly 39 selected target values across 11 locale catalogs; the German catalog has no selected change. All 35 carried holds and all 180 earlier selected-source reattestations are preserved. Source placeholders, markup, numeric tokens, and protected literals pass. All catalogs retain 5,441 keys in the pinned order.

The audit and application are pinned to PR #204 head `7ca8589266ab4c5a925782a8726d7e57b4ed7427`, tree `09adcb271a2eb92770df4a20098dccc3fde2a59f`. The PR base recorded by GitHub differed from live `main`; that divergence is recorded in the audit and preflight evidence. No rebase was performed. No source caller or workflow file changed.

## Contents and verification

- `candidate-free-input/`: frozen exact-head catalog, source, caller, hold, and selection inputs.
- `primary-review/`: primary review ledger and evidence.
- `independent-review/`: independent blind review ledger and evidence.
- `cross-audit/`: sealed third-party adjudication and its embedded copies of original review packets.
- `application/`: byte-identical before catalogs, exact update plan, all-cell readback, key/order invariants, carried-hold and prior-selection readbacks, and verifier.

From the repository root, run:

```sh
python3 docs/pr-evidence/pr204-localization-2026-11-03/window-1423-1442/verify_window_bundle.py
```

This checks the complete portable bundle and runs the application verifier. Qualified native-speaker approval and exact-head product-browser acceptance remain pending. No tests, builds, scans, CI dispatches, workflow edits, merges, releases, or tags were performed for this window.
