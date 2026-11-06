# Independent semantic review: source indices 203–222

This exact-head review covers 20 source keys and all 240 populated translations across 12 locales. It pins the review baseline to `6a8415d2df2f22935188992e03c4636052de2d67` / tree `f562ac9ed6108921efbef4272973b8895bb4c22a`, the direct-child catalog application to `cea88305885c27879ecd1569944ee86bdf78e2b2` / tree `6f2e6881ca7c463eab8e39b9ea3ec08bf929be97`, and source/runtime caller context to `7ff454828398de6a3cfb72fe7f0ed21fe419425b` / tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`.

The exact overlap partition at review head is 39 fresh cells, 104 accepted carries, and 97 prior correction-needed cells, with zero exact-status conflicts. All 39 fresh cells were reviewed: 38 accepted unchanged and one Arabic correction applied. We applied 85 exact-hash prior corrections and held 12: eight Brazilian Portuguese adversarial-security terms and four Simplified/Traditional Chinese adversarial profile/resilience terms. Those held values retain their exact current hashes and prior correction-needed evidence. No cells were left with an unresolved status conflict.

The 86 catalog corrections touch 12 locale JSON files and only the selected cells. They cover the Advanced settings tab label; the security/privacy/anonymity family for adversarial features; two Japanese and Korean labels whose literal readings were misleading in their callsite contexts; Vietnamese removal of invisible zero-width characters; and seven Agreement labels rendered in a numeric opinion-consensus context. The Arabic helper “Advanced privacy and anonymity features” was changed from wording that literally referred to “his identity” to a direct privacy/anonymity phrase. Exact source, old-target, proposed-target, caller, and application pins are in `applied-corrections.jsonl`.

The parent independently cross-reviewed all 86 exact corrections: 85 were accepted as applied and one Arabic `Adversarial Profile` target was refined. The separate follow-up is documented in `../root-cross-review-203-222-follow-up-2026-11-02/`; the 86-row application ledger and original catalog commit remain unchanged.

`selection-before-corrections.jsonl` records every exact baseline target and exact prior disposition. `selection.jsonl` records all final targets and decisions. `decisions.jsonl` contains all 39 fresh-cell decisions; `reviewed-cell-audit.jsonl` contains the semantic/context, placeholder, ICU, protected-literal, and target-hash disposition for every one of the 240 cells. `carries.jsonl` records 104 exact accepted carries; `terminal-exclusions.jsonl` records 12 unchanged exact correction-needed values. `conflict-holds.jsonl` is empty.

The source excerpts and context map in `source-context.txt` are pinned by Git blob ID and SHA-256. The 794-file exact-overlap input manifest is included so the terminal status scan can be reproduced against the frozen prior-audit archive. No placeholders or ICU messages occur in this source window; no protected literals were changed. Native-speaker approval is not claimed; overall locale-quality confidence remains moderate without it.

Headed visual review is blocked because the exact worktree has no `web/node_modules`, and a preview would require installing/building dependencies or using a shared API daemon. Neither was used. The batch changes translation strings only; browser recapture remains required when an isolated exact-branch preview is available. See `headed-visual-check.md`.

No tests, builds, CI, workflow edits, releases, or tags were performed.

## Evidence files

- `manifest.json`: exact review, source, and application pins; coverage counts; locale catalog hashes; scan checksum; visual blocker.
- `selection-before-corrections.jsonl`, `selection.jsonl`: all 240 exact source/target cells before and after.
- `decisions.jsonl`, `reviewed-cell-audit.jsonl`: fresh decisions and complete 240-cell review records.
- `carries.jsonl`, `terminal-exclusions.jsonl`, `conflict-holds.jsonl`: exact unchanged terminal dispositions and holds.
- `applied-corrections.jsonl`: 86 exact-hash applied corrections.
- `prior-evidence-scan-manifest.jsonl`: all 794 raw prior evidence files and checksums.
- `source-context.txt`: exact caller excerpts and source file pins.
- `headed-visual-check.md`: precise visual-review blocker.
- `verify_batch.py`: independent exact-head, overlap, catalog, source-context, placeholder, and checksum verifier.
- `SHA256SUMS`: checksums for all bundle files except the checksum list itself.

Run the verifier from the PR worktree while the frozen audit archive is available:

```sh
python3 docs/pr-evidence/pr204-semantic-review-2026-11-01/independent-0203-0222-all-12-locales/verify_batch.py \
  --repo "$PWD" \
  --prior-audit /path/to/slskr-populated-catalog-review-7ff45482-20261101
```
