# slskR PR #204 exact-status conflict adjudication

This bundle resolves the 25 exact-current status conflicts found by the full-catalog scan pinned to PR head `1494972d86c8fddf62078328376d4aefca07f051` / tree `1c0b3e16e721dfe623cf4239ae3bd4f9fbfc86d3`. Runtime context is pinned to `7ff454828398de6a3cfb72fe7f0ed21fe419425b` / tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`.

`prior-conflicts.json` retains every baseline conflict and exact evidence reference. `prior-evidence-file-manifest.jsonl` pins every referenced evidence file; the verifier checks those raw files in the retained overlap archive. `source-contexts.jsonl` records source-code excerpts, line ranges, blob IDs, and hashes. `conflict-resolutions.jsonl` gives one source-linked final disposition for each conflicting source/locale cell and explicitly lists every exact prior record it supersedes.

## Adjudication

- 8 cells are accepted: the Arabic, German, and Spanish `Item Recs` labels accurately match the `loadItemRecommendations` button; five Korean API messages preserve the exact `username` and `password` identifiers and describe the validation conditions.
- 15 cells remain correction-needed at moderate confidence: Spanish user-note-limit phrasing; four Discovery Graph success-status terms; four Mesh provenance labels; four last-seen timestamp messages; and two Chinese RustyMilk active-preset labels. The proposals and source-context rationales are recorded per cell. These remain unapplied pending stronger locale confidence.
- 2 high-confidence cells are corrected: the Japanese setup-health status (“A download path is configured”) and Brazilian Portuguese singular API-field wording for `ExternalId`. The two Chinese RustyMilk labels remain unapplied at moderate confidence.

All four `{title}` placeholders in the Discovery Graph cells are retained. No ICU messages occur in these 25 source keys. API identifiers and the RustyMilk product name are checked as protected literals wherever present. No native-speaker approval is claimed.

## Reverification

After the catalog application commit and the evidence commit are on the checkout, run:

```sh
python3 docs/pr-evidence/pr204-semantic-review-2026-11-01/exact-conflict-resolution-1494972d-2026-11-01/verify_conflict_resolutions.py \
  --repo "$PWD" \
  --prior-audit /mnt/disks/scratch/task-worktrees/localization-20261030/slskr-populated-catalog-review-7ff45482-20261101 \
  --out /mnt/disks/scratch/task-worktrees/localization-20261030/slskr-e05-window5420-audit-20261101/post-conflict-exact-scan.json
```

The verifier confirms the baseline and application trees, exact prior evidence file hashes and line records, every source and target hash, all 25 resolutions, placeholders/protected literals/ICU syntax, the exact catalog diff, and the resulting full-catalog current-head statuses. It requires zero remaining exact-status conflicts. The overlap archive is task scratch and is retained read-only.

The catalog application is commit `94d67e7deaf418120294c2ff6681c2773fb8c023` (tree `b6d9a9b012e65eb87daed63192d800445de0c726`), whose parent is the reviewed baseline. This pass does not run tests, builds, CI, workflows, releases, or tags.
