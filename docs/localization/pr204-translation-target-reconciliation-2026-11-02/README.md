# PR #204 current target hashes for the 6,588-cell source audit

This reconciliation preserves the original translation review ledger as historical evidence and checks its targets against the current semantic-review catalog snapshot. The exact catalog commit is `ad7c283dfe84f31b52f5a27c363a605fe068e36c` / tree `d0a2faeba016b57850767fe0903b67621d61bc6c`. The source manifest is `docs/localization/pr204-pending-translation-cells-9c6dcb22.jsonl` (SHA-256 `027ba04ae68b21057b305650cc3523108686114fd16964f88ef31b12e89be835`); the original 6,552-cell translation ledger is `docs/localization/pr204-translation-review-2026-11-01.jsonl` (SHA-256 `27ab430e61b7cb5628150121afc1b565e38af9cd2dc2608d3aebd65fce99220e`).

The 549 source IDs expand to 6,588 locale targets. At the current catalog commit all target cells are present, non-empty, and different from their English source strings. Of the 6,552 rows in the historical translation review ledger, 6,524 target hashes still match. The other 28 are superseded by one exact applied semantic-correction row apiece, with source, old-target, current-target hashes and evidence line hashes pinned in `changed-target-supersessions.jsonl` (SHA-256 `120d405dec7474cbea941e0df8f17e0ef1f7dd9df7c97a010b73e0cf6f98c0a7`). The three enum display IDs add 36 target cells outside that 6,552-row ledger; they are checked for presence and non-source-identical values.

`reconciliation-summary.json` records all 12 current catalog file hashes and the counts above. SHA-256: `d53230d5a70d846da551742c57a146f9b8df0fc15d275e98b51a87284734f4be`. Native-speaker approval is false. The original ledger is not rewritten and superseded target hashes are not counted as new accepts.

Run the verifier from the repository root to recompute the audit and compare its deterministic evidence files:

```sh
python3 docs/localization/pr204-translation-target-reconciliation-2026-11-02/verify_translation_target_reconciliation.py --repo "$PWD"
```

To regenerate the exact supersession ledger and summary from the pinned catalog and committed semantic correction evidence, add `--write-evidence`. Verifier SHA-256: `e6b79814967f89301cef14f77c2362a1a43c687085d849ca04d24bce493666a4`. `SHA256SUMS.txt` covers every file in this directory except itself.
