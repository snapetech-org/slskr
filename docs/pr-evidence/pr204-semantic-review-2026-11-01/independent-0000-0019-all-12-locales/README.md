# Independent semantic review: source indices 0–19

This bundle reviews the first 20 source IDs in zero-based Python lexical order from the 5,437-key catalog at PR #204 code head `7ff454828398de6a3cfb72fe7f0ed21fe419425b` (tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`). The review was prepared against PR evidence head `36c98eceea4c8cd016b2fe5092e563b17fcf3f32` (tree `bfe3d3cfbb4c2bb1eda75c29833028d72492bf3c`); code and catalog trees match the frozen source snapshot.

The 240 populated cells partition into 76 fresh decisions and 164 exact prior terminal matches. Fresh decisions: 69 accepted and 7 correction-needed. Prior matches: 112 accepted carries, 45 correction-needed exclusions, and 7 held exclusions. The combined disposition totals are 181 accepted, 52 correction-needed, and 7 held. There are no exact-status conflicts or fresh cells with exact terminal overlap.

## Fresh findings

The review found seven correction candidates; none were applied to catalogs in this evidence pass:

| Source index | Locale | Finding |
| ---: | --- | --- |
| 13 | Arabic | The translated `Precision` fragment omits its leading separator. Proposal: `، الدقة=`. |
| 14 | Arabic | The translated `Warnings` fragment omits its leading separator. Proposal: `، التحذيرات:`. |
| 15 | Arabic | The alternative credential guidance omits the leading separator. Proposal adds `،` before `أو`. |
| 15 | German | “Connect” remains in English although the UI label in the same catalog is `Verbinden`. |
| 15 | French | “Connect” remains in English although the UI label in the same catalog is `Connecter`. |
| 15 | Hindi | The control label is transliterated as `कनेक्ट`, while the UI label in the same catalog is `जोड़ना`. |
| 17 | German | `{childDirectoryCount}-Ordner` should use a space before the plural noun: `{childDirectoryCount} Ordner`. |

All other fresh cells preserve the source meaning in their callsite, dynamic placeholders, ICU status, and relevant visible markers. The 7 held cells are exact prior dispositions: Hindi `% of Response` remains held for response-fragment composition context; six translations of the long DHT bootstrap-router fragment remain held for context. The held cells were excluded from fresh semantic decisions.

The 6,588 cells from the separate source-linked error/UI audit are not missing translations: at this frozen catalog snapshot all 12 locales have 549/549 populated, non-empty, non-source-identical target cells. This batch is semantic review of a disjoint catalog window, not a missing-value report.

## Evidence files

- `selection.jsonl` records the 240 selected cells and their exact prior references.
- `decisions.jsonl` contains the 76 fresh per-cell semantic dispositions and proposals.
- `carries.jsonl` contains the 112 exact accepted carries.
- `terminal-exclusions.jsonl` contains the 52 exact correction-needed or held exclusions.
- `prior-evidence-scan-manifest.jsonl` pins all 706 prior evidence inputs used for overlap detection.
- `source-context.txt` records the runtime callsites at the pinned source head.
- `manifest.json` pins repository, PR, source, catalog, context, overlap, and per-cell counts.
- `verify_batch.py` verifies the pins, catalog cells, overlap references, counts, context, and checksums.
- `SHA256SUMS` hashes every other file in this bundle.

To re-run the verifier, provide the audit worktree that contains the pinned prior audit inputs and the current PR worktree:

```sh
python3 verify_batch.py --repo /path/to/slskR-worktree --prior-audit /path/to/slskr-populated-catalog-review-7ff45482-20261101
```

The verifier reads only the paths listed in the retained input manifest and checks each file's byte count and SHA-256 before reconstructing exact source/target hash overlaps. A failure means the retained audit inputs, exact code/catalog head, or bundle bytes differ from the recorded evidence.

No catalog/source files, tests, builds, CI jobs, workflows, releases, or tags were changed or run in this pass. Correction suggestions do not by themselves establish native-speaker approval or require a browser recapture.
