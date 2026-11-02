# Independent semantic review: source indices 283–302

This exact-head review covers 20 populated source keys and all 240 target cells across 12 locales. It pins the review baseline to PR #204 head `aa604d3ae8e32ae997c97e12a210f20be92cdd5f` / tree `5cdb9fe6a6e25c8921767ebd11f5a19e338c7fbc`, the source catalog and caller snapshot to `7ff454828398de6a3cfb72fe7f0ed21fe419425b` / tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`, and the 43-cell catalog correction commit to direct child `af582e74c5c020e267dd8945e1e70bb4be745f0f` / tree `1f4b4bcfc48ef7dfebbfa4ab1eb97e68437ab640`.

At the review head, the exact overlap partition was 60 fresh cells, 147 exact accepted carries, and 33 prior correction-needed values, with zero exact-status conflicts. All 240 current values were reviewed against their source meanings and caller context, including placeholders, ICU syntax, and protected product literals. The fresh set yielded 50 accepted unchanged and 10 corrections. Root independently cross-reviewed all 43 hash-pinned candidates: 42 accepted as proposed and one refined (French source index 290 to `Une erreur s’est produite lors du compactage de la base de données.`). All 43 final targets were applied. The completed window has 197 accepted values and 43 corrected values, with zero holds or unresolved conflicts.

The correction commit updates all 12 locale catalogs and no other paths. Native-speaker approval was not provided; locale-quality confidence remains moderate.

Headed visual review remains blocked: the exact review checkout has no `web/node_modules`, and an isolated preview would require dependency installation/build output. No dependencies were installed and no build was run. Browser recapture is required when an exact-branch preview is available through the Agentic VM.

No tests, builds, CI, workflow edits, releases, or tags were performed. `git diff --check` passed for the catalog patch.

## Evidence files

- `selection-before-corrections.jsonl`, `selection.jsonl`: exact baseline and final selected cells.
- `decisions.jsonl`, `reviewed-cell-audit.jsonl`: fresh dispositions and the complete 240-cell audit.
- `carries.jsonl`, `terminal-exclusions.jsonl`, `conflict-holds.jsonl`: accepted carries and empty unresolved sets.
- `applied-corrections.jsonl`: all 43 exact-hash updates and application pins.
- `candidate-corrections.jsonl`, `candidate-main-input.jsonl`, `candidate-supplement.jsonl`, `root-cross-review.jsonl`, `root-apply-plan.jsonl`: candidate proposals, exact root dispositions, and approved final text.
- `prior-evidence-scan-manifest.jsonl`: checksums for all exact-overlap evidence inputs.
- `source-context.txt`, `source-pins.json`: pinned source callsites, catalogs, and Git blobs.
- `headed-visual-check.md`: visual review blocker.
- `manifest.json`, `SHA256SUMS`: exact pins and checksums.
- `verify_batch.py`: reproducible overlap, source, catalog, application, placeholder, and checksum verifier.

Run the verifier from a checkout containing the pinned commits and frozen audit archive:

```sh
python3 docs/pr-evidence/pr204-semantic-review-2026-11-01/independent-0283-0302-all-12-locales/verify_batch.py \
  --repo "$PWD" \
  --prior-audit /path/to/slskr-populated-catalog-review-7ff45482-20261101
```
