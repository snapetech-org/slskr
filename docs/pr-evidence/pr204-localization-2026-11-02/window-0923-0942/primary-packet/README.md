# slskR PR #204 primary semantic review — W923–W942

Reviewed 20 sorted source IDs × 12 direct locales (240 cells) at exact open/draft PR head ca71c6c90cbe6c1fa9ef0307a57b214e61e022b5, tree a35194c508f9b40f28ed75480fc20182a086c55d. All twelve catalogs have the same ordered 5,441-key set and their file/blob hashes are pinned. The selection-time GraphQL snapshot covers all seven localization PRs.

Primary dispositions: {'correction': 40, 'accept-current': 186, 'refinement': 2, 'hold': 12}. The 12 held cells are the catalog-only “Copy a short report of these browser-local choices to include with a support request.” source; no exact production source-literal caller exists at this head. The other 19 source IDs have pinned caller context.

The review proposes 42 value changes across copy-action labels, graph terminology, network-peer wording, and side-effect guarantees. Two current protected-literal cells alter the SongID name (German Song-ID; Hindi transliteration); both final proposals preserve exact SongID and JSON. ReplayGain and Servarr are preserved. All final targets have exact placeholder and markup parity and compatible terminal punctuation.

The prior W903–W922 evidence checksums pass. All 240 previous final readbacks still match current catalogs, including the 12 held cells. W922 final values and W923 starting values match prior readbacks/pins for all twelve locales. W943 forward-boundary values are pinned.

This is a static machine-assisted primary review packet, with moderate overall confidence. It does not establish native-speaker approval, headed browser acceptance, or runtime validation. No repo files changed; no tests, builds, scans, CI jobs, or browser actions ran.

## Files

- review-cells.jsonl — all 240 source-locale decisions with source/current/proposed/final hashes.
- source-caller-pins.jsonl and caller-gaps.jsonl — exact caller/context pins and the catalog-only gap.
- catalog-pins.jsonl and protected-literal-integrity.jsonl — twelve catalog hashes and per-cell literal checks.
- boundary-pins.jsonl and prior-disposition-reattestation.jsonl — W922/W943 boundaries and previous final dispositions.
- locale-formality-checks.jsonl and glossary-reference-pins.jsonl — register and same-head terminology evidence.
- all-seven-pr-snapshots.json, live-head.json, and final-live-head.json — selection and final head attestations.
- summary.json, prior-boundary-reattestation.json, terminology-sources.md, and manifest.json — review counts, limits, and packet metadata.
- build_primary.py — reproducible packet builder.
- SHA256SUMS — checksums for packet files, including manifest.json.

Native-speaker approval is not claimed; the catalog-only caller gap remains held.
