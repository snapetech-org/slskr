# Independent blind semantic review — slskR PR #204 W1163–W1182

Reviewed from the checksum-verified candidate-free input packet at `/mnt/disks/scratch/task-scratch/slskr-pr204-w1163-1182-clean-input-20261103/clean-input`. The live head/tree pins recorded in that packet are `9aa58492ee693d8ca0f2c027a3ee5b8438639f91` / `b9ebab27d1f24932be0c623cf894a78115b6f2bb`. This ledger covers 240 cells: accept-current=182, correction-proposal=22, hold=4, refinement-proposal=32.

## Holds

- Position 1165, `Discovered`, Arabic: the current imperative conflicts with the source state label. A safe Arabic form depends on the omitted noun and number agreement; hold for native review.
- Position 1179, `Discovery caution`, `zh-Hans` and `zh-Hant`: the current 警告 means warning, while the rating dimension could mean caution/preference; the packet includes no glossary to settle the distinction.
- Position 1180, discovery refresh counts, Arabic: number agreement depends on the runtime count and counted noun. Hold pending a native Arabic wording review.

## Mechanical checks and limits

All 240 current cells preserve the source placeholder multiset. Every proposed value preserves the same placeholders and source markup; this window has no markup tags. When present, exact `DHT` and lowercase `slskr` literals are preserved. The candidate-free packet had no separate protected-term glossary; `DHT` and `slskr` were treated as fixed from their protocol/product use in the pinned source contexts. `Discovery Graph` and `Discovery Shelf` are treated as localizable UI feature labels.

Confidence is lower for Arabic, Hindi, Japanese, Korean, Vietnamese, and Chinese idiom/register. This machine-assisted review is not native-speaker approval. No repository/PR changes or tests/builds/CI were made.

## Input packet hashes

- `current-target-cells.jsonl`: `0a753fa2647ddcd6b902749fbb46392c757d090c72805f9fa274796b1130ddc4`
- `source-contexts.jsonl`: `7bb077329c5fb283898520749e222f3e165422cf0a27bd20d8b30fb8fbc56210`
- `manifest.json`: `e8fd206298f2685d5126f61aa55c8186192a35e3dbb76f3ccd44ca4833f69422`
- `catalog-file-pins.json`: `fb5c91d4fa97cd68e6b1627041b1a101423cac26de58658c695ea33a17f1a532`

The complete review ledger is `blind-decisions.jsonl`; `summary.json` records counts and exact holds.
