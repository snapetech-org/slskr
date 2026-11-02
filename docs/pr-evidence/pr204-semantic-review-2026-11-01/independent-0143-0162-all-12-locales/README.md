# Independent semantic review: source indices 143–162

This bundle covers 20 source keys and all 240 populated locale cells. The source catalog was lexically pinned at `7ff454828398de6a3cfb72fe7f0ed21fe419425b` / tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`; the reviewed current catalog baseline is PR #204 head `82494e758b7a78abd34812264a57a2a80bcc4c5c` / tree `ab984cf0c7043479b07264ccede7800c46d71db2`. Eight high-confidence exact-hash corrections were applied in catalog commit `f4d5d8818028162266e56d027b7966f300bb6474` / tree `c4a4f0d55c8d206d19fe7c1b15f9b661f48e82a7`. The evidence/docs commit follows that catalog commit, so the verifier uses the pinned application tree rather than a self-referential docs head.

The 240-cell partition is 87 fresh reviews (84 accepted, 3 correction-needed), 103 exact accepted carries, 42 exact correction-needed exclusions, 8 exact-hash corrections applied, and 0 conflict holds. Fresh reviews have no terminal exact prior status. All source/target hashes and the complete locale values are retained.

At the original review head, three fresh moderate findings were recorded: French `Active Swarm Downloads`, French `Add Forwarding`, and Hindi `Add Item to`. A second exact-context review accepted and applied all three high-confidence fixes in commit `e3b1667bcec64e3b41c124e66ea6b29cc88102b9` / tree `baa6d9cb0a7683372c7a6130aa10147b0c880141`: `Téléchargements multi-sources actifs`, `Ajouter une redirection de port`, and `आइटम जोड़ें:`. The context, exact hashes, independent dispositions, and three-cell-only application verifier are in [`cross-review-corrections-0143-0162-2026-11-01`](../cross-review-corrections-0143-0162-2026-11-01/).

Eight previously reviewed high-confidence corrections are applied: the Indonesian invite noun, six `Add Hated` list-action labels, and Arabic `Add Interest`. Each row pins the exact pre-application source/current-target hashes, exact prior correction-needed records, proposal hash, and resulting catalog target hash. Lower-confidence earlier correction suggestions in this window remain excluded and unapplied.

The verifier rechecks the review/application/source commits and trees; exact catalog hashes; exact 240-cell overlap partition; raw prior-evidence inputs; target/source hashes; eight applied changes; placeholders, ICU, protected literals, runtime source excerpts, and checksums. This is independent machine semantic review; it does not claim native-speaker approval. No tests, builds, CI, workflows, releases, or browser recapture were performed.

## Evidence files

- `selection.jsonl`: final current value for all 240 cells at the application commit.
- `selection-before-corrections.jsonl`: exact baseline values and overlap statuses at the review head.
- `decisions.jsonl`: all 87 fresh per-cell semantic decisions.
- `carries.jsonl`: 103 exact accepted carries.
- `terminal-exclusions.jsonl`: 42 correction-needed exclusions.
- `applied-corrections.jsonl`: 8 high-confidence exact-hash catalog changes.
- `conflict-holds.jsonl`: 0 exact conflict holds.
- `prior-evidence-scan-manifest.jsonl`: 763 exact prior evidence files.
- `source-context.txt`, `headed-visual-check.md`, `manifest.json`, `verify_batch.py`, and `SHA256SUMS`: source excerpts, visual-check blocker, run metadata, independent verifier, and checksums.

Run from the PR worktree with the pinned commits available:

```sh
python3 verify_batch.py --repo "$PWD" --prior-audit /mnt/disks/scratch/task-worktrees/localization-20261030/slskr-populated-catalog-review-7ff45482-20261101
```
