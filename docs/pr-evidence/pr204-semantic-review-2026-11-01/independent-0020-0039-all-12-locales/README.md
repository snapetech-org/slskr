# Independent semantic review: source indices 20–39

This bundle reviews source IDs 20–39 in zero-based Python lexical order from the 5,437-key catalog. The exact review head is PR #204 evidence commit `0a75de663b5fe26fea017cec60cc1151f51e1c81` (tree `5411a445b8aacadd2a37081ca516fda001707204`); the reviewed source/catalog snapshot is `7ff454828398de6a3cfb72fe7f0ed21fe419425b` (tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`).

The 240 populated cells partition into 71 fresh decisions and 169 exact prior terminal matches. All 71 fresh cells were accepted. The prior matches include 138 accepted carries and 31 correction-needed exclusions. Combined dispositions are 209 accepted and 31 correction-needed; there are no held cells, exact-status conflicts, or fresh cells with an exact terminal overlap.

Fresh decisions cover the peer-activity and security conditions, chapter/port arrow fragments, MediaCore focused-workflow instructions, empty channel copy, graph-node continuation, byte units, a normalized audio-sample example, and time/beat labels. The reviewed callsites and their exact source hashes and Git blob IDs are in `source-context.txt`. The Arabic `180 د` history label is consistent with the same component's `7d`, `30d`, and `90d` labels (`7 د`, `30 د`, and `90 د`); those sibling options all represent day ranges in `CompatibilityDashboard.jsx`.

The fresh review found no correction candidate. All dynamic placeholders, arrows, numbers, list markers, punctuation fragments, and relevant unit meanings were checked against runtime use. Review confidence is moderate; no native-speaker approval is claimed. No catalog/source changes or browser recapture were required.

## Evidence files

- `selection.jsonl` records all 240 cells, their hashes, and exact prior references.
- `decisions.jsonl` contains the 71 fresh per-cell semantic dispositions.
- `carries.jsonl` contains the 138 exact accepted carries.
- `terminal-exclusions.jsonl` contains the 31 exact correction-needed exclusions.
- `prior-evidence-scan-manifest.jsonl` pins 712 prior evidence inputs used for overlap detection.
- `source-context.txt` records runtime callsites at the source/catalog head.
- `manifest.json` pins repository, PR, code, catalog, context, overlap, and cell counts.
- `verify_batch.py` verifies the pins, catalog cells, exact overlap references, counts, context, and checksums.
- `SHA256SUMS` hashes every other file in this bundle.

Run the verifier with the prior audit worktree and a slskR worktree containing the pinned commits:

```sh
python3 verify_batch.py --repo /path/to/slskR-worktree --prior-audit /path/to/slskr-populated-catalog-review-7ff45482-20261101
```

The verifier rehashes the 712 listed prior evidence files and reconstructs exact source/target hash matches. It fails if input files, code/catalog pins, reviewed targets, or bundle checksums differ.
