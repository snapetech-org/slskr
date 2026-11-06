# slskR PR #204 W1283–W1302 root cross-audit

This packet reconciles 240 cells across 20 source strings and 12 locales at exact PR head `55ca2ae0788bfd79daab5cc49f49ebb608593e98`, tree `d5677673b766d572102bba249af2ab69095dea0d`.

- Final dispositions: 95 accept-current, 73 corrections, and 72 refinements; there are no caller-resolution holds.
- 145 exact target changes are selected. The input packet pins 37 production caller references across six files.
- Two existing Hindi FTP literals were transliterated in the current targets. The selected values restore the protected `FTP` literal.
- Source and target placeholders, markup, numeric tokens, and protected literals were checked per cell. Exact current values are retained where no change is selected.
- The French HTTP policy sentence combines the blind review’s request-rate precision with the primary review’s translation of “mesh gateway.”
- No native-speaker approval is claimed.

Packet checksum-list hashes:

- Candidate-free input: `abbb1b89549b82072fcbf5fce3c6ae580cc5bd499b4fe5dadd5df7bd0c567f89`
- Primary review: `e824b4518481fa2a4b122f3d8c425be7cb22826aa7133ac0e5ec4f1edef9f339`
- Independent blind review: `83d0867a1c615665f2c12609dd2ca525013b438497f8c8309565d0ed6f6e1178`

Run `python3 verify_cross_audit.py` from this directory. It verifies the three source packets, exact source/caller/catalog lineage, selected target hashes, structural tokens, disposition counts, and root packet checksums. `build_cross_audit.py` records the root’s per-cell decisions and selected targets.
