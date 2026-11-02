# Independent semantic review: source indices 63–82

This bundle reviews source IDs 63–82 in zero-based Python lexical order from the 5,437-key catalog. The exact PR #204 review head is `9650a6f9ef70bf23a0dc861156e751729c7a4604` (tree `f2fcb8b930ea9e594b677ded121e6b3324cfd3b8`); the reviewed source/catalog snapshot is `7ff454828398de6a3cfb72fe7f0ed21fe419425b` (tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`).

The 240 populated cells partition into 83 fresh decisions, 138 accepted carries, 14 correction-needed exclusions, and 5 cells with conflicting exact prior outcomes. The fresh review found 79 accepted cells and 4 correction candidates. The prior conflicts are not assigned a new terminal outcome in this bundle: four locales conflict for `; provenance` (ko/vi/zh-Hans/zh-Hant), and Japanese `A download path is configured.` also has contradictory accepted/correction-needed records. These five cells remain for separate adjudication.

## Correction candidates

Suggestions are recorded for later reconciliation and have not been applied to catalogs.

| Source index | Locale | Current text | Suggested text | Finding |
| ---: | --- | --- | --- | --- |
| 65 | French | `:F1=` | `: F1=` | The metric fragment loses the source space after the colon. |
| 66 | Hindi | `: हस्ताक्षर है` | `: हस्ताक्षर की स्थिति` | The following localized `Valid`/`Invalid` value makes the current word order ungrammatical. |
| 70 | Hindi | `; गवाहों` | `; गवाहों की संख्या` | This label is followed by a witness count; the proposal forms a natural “witness count N” phrase. |
| 79 | German | `ALLES STANDARDMÄßIG DEAKTIVIERT` | `ALLES STANDARDMÄSSIG DEAKTIVIERT` | All-caps German writes `ß` as `SS` or `ẞ`; the current all-caps label contains lowercase `ß`. |

The all-caps German spelling is supported by the [2024 official German orthography rules](https://www.rechtschreibrat.com/DOX/RfdR_Amtliches-Regelwerk_2024.pdf), which permit `SS` or capital `ẞ` in uppercase text. The suggested `SS` form avoids font support concerns.

The other fresh cells cover 90-day history ranges, F1 metrics, signature verification, mesh-evidence metadata, acquisition failure status, AI heuristics and mentions, adversarial settings, and API policy labels. Runtime snippets and source hashes are in `source-context.txt`. The Arabic 90-day abbreviations match the same component's 7/30/180-day conventions. Hindi `CIDR` is transliterated consistently with the related `API key CIDR allowlist` label. No native-speaker approval is claimed. No catalog/source edits or browser recapture were performed.

## Evidence files

- `selection.jsonl` records all 240 cells and exact prior references.
- `decisions.jsonl` contains 83 fresh per-cell dispositions and the four proposals.
- `carries.jsonl` contains 138 exact accepted carries.
- `terminal-exclusions.jsonl` contains 14 exact correction-needed exclusions.
- `conflict-holds.jsonl` records the five cells with contradictory exact prior outcomes without assigning a new terminal status.
- `prior-evidence-scan-manifest.jsonl` pins 724 prior evidence inputs.
- `source-context.txt` records runtime callsites, code hashes, and the German orthography reference.
- `manifest.json` pins source/catalog/review heads, cells, conflict references, counts, and proposals.
- `verify_batch.py` rehashes inputs and verifies current targets, evidence overlaps, counts, context, and checksums.
- `SHA256SUMS` hashes every other file in this bundle.

Re-run the verifier with the prior-audit worktree and a slskR worktree containing the pinned commits:

```sh
python3 verify_batch.py --repo /path/to/slskR-worktree --prior-audit /path/to/slskr-populated-catalog-review-7ff45482-20261101
```
