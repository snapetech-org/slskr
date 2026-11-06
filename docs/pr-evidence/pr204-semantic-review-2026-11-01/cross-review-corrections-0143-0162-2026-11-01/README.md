# Exact cross-review corrections for source indices 143–162

A second exact-context review accepted three moderate findings from the original 143–162 batch as high-confidence corrections. The source keys, old targets, and source/target hashes were revalidated against the catalog immediately before application (`2f7794cec0592ffd1a24490a5441b3ee7d1c728d`, tree `aa0c195ecf045fef9545ddbdc7df4a0da305943b`). The three target changes were applied in the directly parented catalog commit `e3b1667bcec64e3b41c124e66ea6b29cc88102b9`, tree `baa6d9cb0a7683372c7a6130aa10147b0c880141`.

- French `Active Swarm Downloads`: `Téléchargements d'essaims actifs` → `Téléchargements multi-sources actifs`. The pinned jobs card calls these multi-source downloads, and its peer label already uses `Téléchargements multi-sources en cours`; the revised adjective modifies downloads and preserves active status.
- French `Add Forwarding`: `Ajouter un transfert` → `Ajouter une redirection de port`. The button creates a port-forwarding rule, and the same page title uses `Redirection de port`.
- Hindi `Add Item to`: `इसमें आइटम जोड़ें` → `आइटम जोड़ें:`. The exact renderer appends a literal space and then the collection title; this yields the natural heading `आइटम जोड़ें: [collection]`.

`applied-corrections.jsonl` records every before/after value and SHA-256, source hash, exact source context pins, original review status, and independent disposition. The source/caller excerpts and their source-tree pins are in the linked [143–162 review bundle](../independent-0143-0162-all-12-locales/). No other catalog cells changed in this application commit. No tests, builds, CI, workflows, releases, or tags were run.

Verify from a checkout containing the pinned commits:

```sh
python3 verify_cross_review.py --repo "$PWD"
```
