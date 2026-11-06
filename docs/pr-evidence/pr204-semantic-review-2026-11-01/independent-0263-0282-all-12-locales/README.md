# Independent semantic review: source indices 263–282

This exact-head review covers 20 populated source keys and all 240 values across 12 locales. It pins the review baseline to PR head `5a697d84c32043b9a56ab052cdbecc8529db1ade` / tree `923a788e4c22df73380cd498b0f11ab1a182b749`, the source and caller context to `7ff454828398de6a3cfb72fe7f0ed21fe419425b` / tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`, and the 14-cell catalog correction commit to direct child `de509ead1789fe64811b14b63e1a22c14ade6893` / tree `e50004385568ab25e9d3eb5d314654880ef6ae8f`.

At the review head, the exact overlap partition was 25 fresh cells, 204 accepted carries, and 11 prior correction-needed cells, with zero exact-status conflicts. All 240 current values were reviewed against their source meanings and pinned caller contexts, including placeholder sets, ICU syntax, and protected technical/product literals. Root independently cross-reviewed all 14 exact-hash candidates: 8 accepted as proposed and 6 refined; all 14 root-approved final targets were applied. The final window contains 226 accepted values and 14 corrected values, with zero holds or unresolved conflicts.

The correction patch updates eight locale catalogs. The candidate, root-review, apply-plan, and application ledgers record exact source, baseline, and final-target hashes. Native-speaker approval was not provided; locale-quality confidence remains moderate.

Headed visual review remains blocked because the exact branch has no `web/node_modules`, and an isolated preview would require dependency installation/build output. No shared daemon, other worktree preview, desktop, or browser session was used. Browser recapture is required when an isolated exact-head preview can be supplied under the approved JIT setup; see `headed-visual-check.md`.

No tests, builds, CI, workflow edits, releases, or tags were performed. `git diff --check` passed for the catalog patch.

## Evidence files

- `selection-before-corrections.jsonl`, `selection.jsonl`: exact baseline and final selected cells.
- `decisions.jsonl`, `reviewed-cell-audit.jsonl`: fresh dispositions and complete 240-cell audit.
- `carries.jsonl`, `terminal-exclusions.jsonl`, `conflict-holds.jsonl`: accepted carries and empty unresolved sets.
- `applied-corrections.jsonl`: all 14 exact-hash updates and application pins.
- `candidate-corrections.jsonl`, `root-cross-review.jsonl`, `root-apply-plan.jsonl`: proposals, root dispositions, and final approved text.
- `prior-evidence-scan-manifest.jsonl`: checksums for all exact-overlap inputs.
- `source-context.txt`, `source-pins.json`: pinned source callsites and Git blobs.
- `headed-visual-check.md`: visual review blocker.
- `manifest.json`, `SHA256SUMS`: exact pins and checksums.
- `verify_batch.py`: reproducible overlap, source, catalog, application, placeholder, and checksum verifier.

Run the verifier from a checkout containing the pinned commits and the frozen audit archive:

```sh
python3 docs/pr-evidence/pr204-semantic-review-2026-11-01/independent-0263-0282-all-12-locales/verify_batch.py \
  --repo "$PWD" \
  --prior-audit /path/to/slskr-populated-catalog-review-7ff45482-20261101
```
