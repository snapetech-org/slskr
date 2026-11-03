# slskR PR #204 — W983–W1002 source-only input

This packet fixes the primary-review input at exact PR head `09a614a66f1104fe530773fb17c79ed6338aed02` / tree `963f283311ae39dfa5fc289386d99dcc0dac2f90`, branch `codex/slskr-l10n-audit-20261030`. The PR is open/draft. Local worktree, official branch, GitHub PR head, and GitHub commit tree were independently reattested.

The current selection uses the sorted unique source IDs shared by all 12 locale catalogs. Those catalogs each contain 5,441 keys with identical key arrays. The committed W963–W982 evidence at `docs/pr-evidence/pr204-localization-2026-11-02/window-963-982/` records a source-key rename at position 964. Its old key was replaced in place across all 12 catalogs; the current sorted inventory preserves positions 963–982 after that rename. The prior full inventory has 5,440 keys; current differences are the recorded renamed key plus the later `Not configured` key. `Not configured` sorts beyond this selected slice and does not shift the boundary. Current positions 983–1002 are therefore the next 20 IDs, disjoint from the reviewed prior window. A disposition-bearing prior-ledger scan found no previous semantic review for these selected IDs.

`source-only-input.jsonl` contains the selected English source IDs, exact current locale values and hashes, catalog file pins, source placeholders/markup/ICU flags, and exact quoted production source-literal caller contexts where found. It contains no translation proposals or dispositions. `selection-evidence.json` records the boundary reconstruction. The primary review uses these inputs; when no exact production caller can be verified, a cell is held rather than inferred.

No repository or PR files were edited. No tests, builds, scans, CI, or browser activity were run. Native-speaker approval is not claimed.

## Primary review results

The independent review ledger covers all 240 cells across positions 983–1002. Dispositions: {'accept-current': 165, 'correction': 40, 'hold': 24, 'refinement': 11}. Positions 983 and 984 remain held in all 12 locales because no exact production caller was found. Other cells are assessed against the exact caller contexts in the source-only input.

Structural review found zero placeholder, markup, ICU, protected-literal, or terminal-punctuation mismatches in current values or proposed targets. Position 990 retains the `{name}` placeholder. Position 991 preserves the FLAC acronym in all reviewed values. This is machine-assisted review; no native-speaker approval is claimed.

The full prior-evidence scan found no disposition rows for these 20 source IDs. The Cover Traffic header uses a noun-form feature name; its sibling Enable Cover Traffic message at current sorted position 1279 should be reviewed with the same locale term when that source window is reached.

The Cover Traffic term is treated as privacy traffic used to obscure traffic patterns; a primary networking-security paper describes it as dummy packets mixed with real data ([TARANET, IEEE EuroS&P 2018](https://people.scs.carleton.ca/~barrera/publications/eurosp18-chen.pdf)). The sibling Enable Cover Traffic label at current sorted position 1279 should use the same locale term when reviewed.
