# Independent semantic review: source indices 83–102

This bundle reviews source IDs 83–102 in zero-based Python lexical order from the 5,437-key catalog. PR #204's exact review head is `0f41d9a694fadd4a29384e8fa1d2927d7941c539` (tree `82fd7fa3bab336ca722fd143d537e905440c3ccb`); the reviewed source/catalog snapshot is `7ff454828398de6a3cfb72fe7f0ed21fe419425b` (tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`).

The 240 populated cells partition into 38 fresh decisions, 103 exact accepted carries, and 99 exact correction-needed exclusions. The fresh review accepted 36 cells and found two German compound-spacing corrections. There are no conflicts or fresh exact-terminal overlaps. Carried/excluded findings keep their existing dispositions and are not duplicated as new review results.

## Correction candidates

Suggestions are recorded for later reconciliation and have not been applied to catalogs.

| Source index | Locale | Current text | Suggested text | Finding |
| ---: | --- | --- | --- | --- |
| 90 | German | `API Schlüssel-CIDR-Zulassungsliste` | `CIDR-Zulassungsliste für API-Schlüssel` | The current form separates the API abbreviation from `Schlüssel` and obscures the relation; the proposal follows the catalog's established `API-Schlüssel` form. |
| 98 | German | `API Ratenbegrenzungsfenster in Sekunden` | `API-Ratenbegrenzungsfenster in Sekunden` | The accessible label names an API rate-limit window measured in seconds. The proposal follows the catalog's hyphenated compounds `API-Token` and `API-Schlüssel`. |

The reviewed contexts are API key policy fields, API scopes and CIDR settings, a Pushover API-token input, a stored-token toggle, API rate-limit fields, and the accelerated-download toggle. Hindi's `सीआईडीआर` is accepted for this field because the adjacent visible `API CIDRs` label uses the same transliteration, while `API` remains in Latin script. No native-speaker approval is claimed. No catalog/source edits, tests/build/CI, or browser recapture were performed.

## Evidence files

- `selection.jsonl` records all 240 cells and exact prior references.
- `decisions.jsonl` contains 38 fresh per-cell dispositions and the two proposals.
- `carries.jsonl` contains 103 exact accepted carries.
- `terminal-exclusions.jsonl` contains 99 exact correction-needed exclusions.
- `conflict-holds.jsonl` is empty; this window has no exact-status conflicts.
- `prior-evidence-scan-manifest.jsonl` pins 731 prior evidence inputs.
- `source-context.txt` records runtime callsites, code hashes, and the Hindi cross-label evidence.
- `manifest.json` pins heads, catalogs, window counts, source context, and proposals.
- `verify_batch.py` rehashes inputs and verifies targets, overlaps, counts, context, and checksums.
- `SHA256SUMS` hashes every other file in this bundle.

Re-run the verifier with the prior-audit worktree and a slskR worktree containing the pinned commits:

```sh
python3 verify_batch.py --repo /path/to/slskR-worktree --prior-audit /path/to/slskr-populated-catalog-review-7ff45482-20261101
```
