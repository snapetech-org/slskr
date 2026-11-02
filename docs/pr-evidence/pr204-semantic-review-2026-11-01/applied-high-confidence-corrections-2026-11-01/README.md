# Applied high-confidence semantic corrections

This bundle records eleven disjoint high-confidence corrections from the completed source-key windows 0–19, 43–62, 63–82, and 83–102. Before changing any value, the application script verified each source hash and exact current-target hash against PR head `cb1fc0c0d51ff6cf136862429530399755763bb3`, checked placeholder parity, and rejected duplicate source/locale cells. It changed only those eleven catalog values across Arabic, German, Spanish, French, and Hindi.

`applied-corrections.jsonl` is the refreshed current-target ledger. Its `target_sha256` values hash the replacement targets and its terminal status is `corrected`, so exact-current coverage rescans recognize the new targets. Each row points to the original high-confidence correction decision and its prior target hash. The manifest records before/after hashes for all twelve catalogs. Moderate-confidence suggestions remain unapplied. No native-speaker approval is claimed.

Run the standalone verifier after checkout of the application commit:

```sh
python3 verify_corrections.py --repo /path/to/slskR-worktree
```
