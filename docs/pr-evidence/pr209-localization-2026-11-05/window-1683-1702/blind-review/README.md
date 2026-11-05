# Blind review ledger: slskR PR #209 W1683–W1702

This ledger records an independent semantic review of all 240 cells (20 source strings × 12 locales). It was built using only the candidate-free input packet at `/mnt/disks/scratch/task-scratch/slskr-pr209-w1683-1702-20261105/candidate-free-input`. The primary-review directory and its proposal strings were not accessed. No catalog, repository, branch, or remote was changed; no build, test, scan, or CI job was run.

## Source pin and evidence

- PR head: `f04b7f965aef79552d65d40a2eeb550e5e3b9cfa`
- Tree: `85fe880023e55e055660fd17599c291edd24a1c6`
- Branch: `codex/slskr-l10n-audit-20261104-resync`; base SHA: `1bbaec9fdc63a86de343e37e33bae70d44301a36`
- Before/after attestations match this source pin, and all input packet SHA256 checks passed.
- `ledger.jsonl` contains exactly one decision for every position/locale pair. It includes the exact current target, its SHA-256, source key and hash, catalog file SHA/Git blob, caller paths/line text and hashes, and token-check metadata.
- `caller-evidence.jsonl` retains all 20 candidate-free caller contexts. `holds.jsonl` is empty because the packet reports no callerless positions and all 240 current target texts are included.

## Review result

- Decisions: 235 keep, 5 propose, 0 hold.
- Proposal cells: 1683/ko, 1684/ko, 1685/zh-Hant, 1686/ko, 1692/de.
- The Korean target for position 1683 mistranslates “backfill” as “backup ad”. The Korean targets for 1684 and 1686 drop the colon that separates the label from an appended dynamic error. The Traditional Chinese target for 1685 mixes simplified 注 with traditional characters. The German target for 1692 shifts “affinities” to “assignments/mappings”. Exact replacements are in the relevant ledger rows.
- All named placeholders are present; 12 cells reorder them for locale grammar, and the runtime replaces them by name. Markup and numeric tokens match. The two protected-token mismatches are generic “ID” localized as identifiant / معرّف; they are accepted. YAML is preserved in all 12 locales.
- Confidence is high for the four clear typo/mistranslation/punctuation proposals and moderate for the German affinity terminology proposal and unchanged translations generally.

## Verification and seal

Run:

```bash
python3 verify_blind_ledger.py --input-dir /mnt/disks/scratch/task-scratch/slskr-pr209-w1683-1702-20261105/candidate-free-input --output-dir /mnt/disks/scratch/task-scratch/slskr-pr209-w1683-1702-20261105/blind-review-codex-20261105
sha256sum -c SHA256SUMS.txt
```

`SHA256SUMS.txt` covers the ledger, summary, caller evidence, README, verifier, empty holds file, and seal metadata. `seal.json` records the ledger and evidence hashes.
