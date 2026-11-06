# slskR PR #204 W1463–W1482 cross-audit

This packet reconciles all 240 current cells against the primary packet and the clean independent blind packet, using the sealed candidate-free source/caller input. It records every primary and clean-blind proposal, selects a final disposition and target, and accounts for every proposal as selected or superseded. Position 1466 remains held across all 12 locales because the pinned production scan has no exact caller; those rows contain hashes only and omit source/current/proposed target text.

## Reconciliation

- Primary proposals: 44; clean independent proposals: 51.
- Same target proposed by both: 21.
- Different target proposals: 15; each is adjudicated in the ledger with the selected source and rationale.
- Primary-only proposals: 8; all were assessed and dispositioned.
- Clean independent-only proposals: 15; all are included in the ledger, including their target text, and dispositioned.
- No proposal from either review: 181 cells.
- Final decisions: 169 accept-current, 29 corrections, 30 refinements, and 12 holds.

## Token and context results

The current cells have 0 placeholder, 0 markup, 0 numeric-token, and 28 protected-literal mismatches. Sixteen FTP mismatches are repaired in proposed targets; the exact pinned source/caller context identifies the FTP controls. Twelve FAIL mismatches are hash-only holds because position 1466 has no exact production caller. All 59 proposed cross targets pass placeholder, markup, numeric, and protected-literal checks. No current mismatch is accepted.

The ledger pins each source and caller context by hash and caller file/line/blob identifiers. All source/current/proposal text in the ledger comes from the allowed candidate-free, primary, or clean independent packets. Prior selection, prior hold, carry-forward, and source-order-lineage content was not decoded or parsed. The prior continuity file contains only counts, byte counts, and hashes from the candidate-free manifest.

## PR and deployment attestation

PR #204 was OPEN/DRAFT at the pinned head and tree before and after review. The branch and pull refs matched the head at both points. The read-only deployments API query returned zero deployments for this head before and after; no deployment action was issued. Attestation files include the refs and timestamps. The PR API base SHA differs from the current main ref SHA; this same observation persisted before and after and did not change the PR head/tree.

No repository, catalog, or PR files were edited. No tests, builds, scans, CI, or browser actions were run.

## Verification

Run from this directory:

    python3 verify-cross-audit.py
    sha256sum -c SHA256SUMS.txt

The portable verifier uses Python's standard library. It verifies packet checksums by hashing restricted input files without decoding or parsing them, checks all 240 reconciliations and target token rules, verifies hash-only holds, and compares before/after PR/deployment attestations.
