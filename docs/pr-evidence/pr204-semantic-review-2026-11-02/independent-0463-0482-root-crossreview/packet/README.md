# slskR PR #204 semantic review packet: W463–482

This packet reviews the 20 source keys at sorted source-inventory indices 463–482, including all 240 cells across `ar`, `de`, `es`, `fr`, `hi`, `id`, `ja`, `ko`, `pt-BR`, `vi`, `zh-Hans`, and `zh-Hant`.

## Pinned inputs

- Live PR: open, draft, clean/mergeable, branch `codex/slskr-l10n-audit-20261030`.
- PR head: `549bb55fe009246362cfd75e9f5fbfe5a66bb101`; tree `86f59f722e25c1a90d5bc348da68c27247088271`.
- Runtime/source context: `7ff454828398de6a3cfb72fe7f0ed21fe419425b`; tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`, an ancestor of the PR head. The reviewed component source paths are unchanged between those pins.
- Source inventory: 5,437 sorted IDs; SHA-256 `dd5959b45ec3a7002806b3b03a8d434cb791cc737d2afe1554d24351eac6f313`.
- Full current catalog hashes and byte sizes are in `manifest.json`. Every selected row is populated in all 12 catalogs.

`source-context.jsonl` pins the exact callers, line excerpts, file blob IDs, and SHA-256 values. It also records contextual meaning and fixed terms or units adjacent to the translated strings. None of the selected source IDs contains an interpolation placeholder. Context-only names such as Pod and Soulseek are not placeholders.

## Review results

- 240 per-cell decisions are recorded in `decision-ledger.jsonl`.
- 65 exact-current correction candidates from prior evidence were confirmed against the pinned callers.
- 170 cells were retained as currently acceptable.
- Five new context/fluency candidates were identified: Spanish and Indonesian `Batch Descriptor Retrieval`, Korean `Batch Descriptor Retrieval` (reopened from an exact prior acceptance because the caller explicitly retrieves rather than searches), Arabic `Batch Publish Results`, and Spanish `Best Next Actions`.
- The resulting 70 correction candidates include those five additional candidates.
- The overlap join covered 1,023 prior-evidence input files. It found exact source-and-current-target matches for 162 cells, represented by 197 deduplicated evidence records (359 raw records); no conflicting exact proposals were found.
- Source wording suggestions for potentially ambiguous labels are recorded in `source_rewrite_consideration` within each applicable row in `source-context.jsonl`.

The ledger is a review recommendation for root cross-review; it is not native-speaker approval. No catalog was edited. No tests, builds, scans, CI, workflow edits, releases, tags, or merges were run.

## Files

- `manifest.json`: exact live PR, head/tree/source pins, locale catalog hashes, inventory, overlap, and coverage summary.
- `decision-ledger.jsonl`: one record per source/locale cell with current/proposed text, hashes, placeholders, protected-context literals, overlap evidence, disposition, and rationale.
- `source-context.jsonl`: source-key meaning and pinned callsite snippets.
- `prior-evidence-scan-manifest.jsonl`: path, byte size, and SHA-256 for every overlap input.
- `prior-exact-matches.jsonl`: deduplicated exact-current prior review matches with evidence file references.
- `source-inventory.jsonl`, `freeze-manifest.json`, `freeze-manifest.sha256`: frozen source inventory and provenance.
- `prepare_review_window.py`: reproducible packet preparation script.
- `SHA256SUMS.txt`: checksums for all packet files except the checksum file itself.
