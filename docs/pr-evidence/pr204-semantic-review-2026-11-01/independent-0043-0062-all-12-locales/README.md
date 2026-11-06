# Independent semantic review: source indices 43–62

This bundle reviews source IDs 43–62 in zero-based Python lexical order from the 5,437-key catalog. The exact PR #204 review head is `271c782fd27e8c5e33bac0014d87cc7100c1b9bf` (tree `29b89f7145b7a14b71dca0c76168e0bd5d0a5b2e`); the reviewed source/catalog snapshot is `7ff454828398de6a3cfb72fe7f0ed21fe419425b` (tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`).

The 240 populated cells partition into 98 fresh decisions and 142 exact prior terminal matches. The fresh review found 93 accepted cells and 5 correction candidates. Prior matches include 138 accepted carries and 4 correction-needed exclusions. Combined dispositions are 231 accepted and 9 correction-needed. There are no held cells, exact-status conflicts, or fresh cells with an exact terminal overlap.

## Correction candidates

The suggestions are recorded for later reconciliation and were not applied to catalogs in this pass.

| Source index | Locale | Current text | Suggested text | Finding |
| ---: | --- | --- | --- | --- |
| 45 | Hindi | `24 घंटों` | `24 घंटे` | The compatibility range button is a standalone duration label; direct form is natural here and matches the catalog’s `24 hours` translation. |
| 46 | Hindi | `255, 128, 64, ... (आरजीबीए पिक्सेल डेटा)` | `255, 128, 64, ... (RGBA पिक्सेल डेटा)` | Preserve the standard RGBA format acronym as an uppercase technical literal. |
| 54 | Arabic | `4 نبضة` | `4 نبضات` | Arabic counted nouns after numerals 3–10 take the plural form; `نبضة` is singular. |
| 59 | Spanish | `7 dias` | `7 días` | Spanish spelling requires the acute accent in `días`. |
| 62 | Arabic | `8 نبضة` | `8 نبضات` | Arabic counted nouns after numerals 3–10 take the plural form; `نبضة` is singular. |

The Arabic count-noun findings follow the plural rule described by [UC Davis Arabic Without Walls, Grammar Note 7.4](https://arabicwithoutwalls.ucdavis.edu/chapter7/grammar_note74.html) and [Al Jazeera Learning Arabic](https://learning.aljazeera.net/ar/node/19761). The French `4 temps` target is accepted as a music-specific translation for a beat; [Larousse](https://www.larousse.fr/dictionnaires/anglais-francais/beat/564977) lists `temps` for the music/time sense. Neighboring 8- and 16-beat options use `battements`, a style inconsistency without a meaning loss in this context.

The runtime contexts cover FPS quality caps; analytics and history windows; RGBA pixel-data entry; time-based visualizer controls; and detected bass-beat controls. Dynamic values, counts, acronyms, arrows, punctuation, units, and range meanings were checked against their callsites. Review confidence is recorded per cell; no native-speaker approval is claimed. No catalog/source edits or browser recapture were performed.

## Evidence files

- `selection.jsonl` records all 240 cells, hashes, and exact prior references.
- `decisions.jsonl` contains 98 fresh per-cell dispositions and the five proposals.
- `carries.jsonl` contains 138 exact accepted carries.
- `terminal-exclusions.jsonl` contains four exact correction-needed exclusions.
- `prior-evidence-scan-manifest.jsonl` pins 718 prior evidence inputs.
- `source-context.txt` records runtime callsites, code blobs, and language references.
- `manifest.json` pins repository, PR, source, catalog, context, overlap, counts, and correction candidates.
- `verify_batch.py` checks exact pins, targets, overlap references, counts, context, and checksums.
- `SHA256SUMS` hashes every other file in this bundle.

Re-run the verifier with the retained prior-audit worktree and a slskR worktree containing the pinned commits:

```sh
python3 verify_batch.py --repo /path/to/slskR-worktree --prior-audit /path/to/slskr-populated-catalog-review-7ff45482-20261101
```
