# Blind semantic review: slskR PR #204, W1243–W1262

## Scope and result

Reviewed all 240 current target cells for 20 source keys across the 12 runtime locales, using only the candidate-free input packet. The review records 179 accepted cells, 1 correction, 48 refinements, and 12 held cells. The held cells are exactly the 12 locale values for **Ecosystem** at position 1257; no semantic verdict was assigned to them.

Confidence is **moderate** overall. This is an independent semantic review, not native-speaker approval.

## Main findings

- Position 1243 Japanese reverses the preview meaning; it is the single correction. The Vietnamese term is refined from a literal “dry” calque.
- Position 1246 needs clearer dry-run wording in 11 locales; the Japanese wording is accepted. All replacements retain the exact `ReplayGain` literal.
- Duration terminology is refined at positions 1248 and 1251 in Chinese, Japanese, Korean, and Vietnamese. Position 1249 is refined in nine locales to make seconds read clearly as the field unit.
- Position 1258 uses graph-atlas context. Eight labels are refined where the current word suggests a border or outer edge instead of a graph edge.
- At position 1245, the capitalized feature name `Discovery Inbox` is translated/transliterated in Hindi and Vietnamese; both replacements preserve the exact name. Simplified and Traditional Chinese use a person-word for “candidate”; replacements use the item sense.
- Indonesian leaves “Edit” untranslated at positions 1260–1262; replacements use “Sunting”.
- The four server validation messages at positions 1252–1254 and 1256 carry additional parenthetical API-field hints absent from the English source. I accepted them as informative and non-contradictory; their field-name literals are exact across all 12 locales.

## Structural and terminology checks

- Placeholder token sequence: **0 mismatches** across 240 cells. All 12 values for the sole placeholder message preserve `{minutes}` exactly.
- Markup: **no markup or entity tokens** in source or target strings.
- Numeric semantics: all 12 non-negative-size targets preserve the zero-or-greater constraint; all 12 positive-timestamp targets preserve positivity. No target introduces a numeric digit literal.
- Units: all 12 `Duration Seconds` values identify seconds; all 12 duration-spread values preserve the minutes unit. The generic `Duration:` label stays unit-neutral because the callers append seconds or milliseconds.
- Protected literals: `ContentID` and `ReplayGain` are preserved exactly in all corresponding targets. The API field names in the added hints (`descriptors`, `contentId`, `files`, `filename`, `size`, `links`, `name`, `target`) are exact. `Discovery Inbox` is preserved except the Hindi and Vietnamese current values noted above.

## Attestation and blockers

The live PR was rechecked on 2026-11-03: open draft PR #204, head `ce2e7d12f3025f0312df37527b4c270d0eb5bce5`, tree `0ead1eb1678b4df05ca7feec9776c0319d4eefd3`. Both `refs/heads/codex/slskr-l10n-audit-20261030` and `refs/pull/204/head` resolved to that head. The pinned local worktree was detached, clean, and at the expected tree.

All 11 files listed by the candidate-free packet’s `SHA256SUMS.txt` verified successfully. No tests, builds, scans, CI, workflow edits, or repository/worktree changes were made. The only review blocker is the required caller-resolution hold at position 1257.

## Files

- `sealed-ledger.jsonl` — one disposition and rationale per cell, with packet caller references and replacements for the correction/refinements.
- `provenance.json` — input packet, PR/ref attestation, integrity checks, and review scope.
- `SHA256SUMS.txt` — output artifact hashes.
