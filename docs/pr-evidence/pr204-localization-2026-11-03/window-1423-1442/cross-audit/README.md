# slskR PR #204 W1423–W1442 independent cross-audit

This portable packet independently adjudicates all 240 locale cells against the candidate-free source, exact production caller excerpts, primary review, and blind review. Pinned PR head: `7ca8589266ab4c5a925782a8726d7e57b4ed7427`; tree: `09adcb271a2eb92770df4a20098dccc3fde2a59f`.

## Results

- Decisions: **201 accept-current, 38 correction, 1 refinement, 0 hold**.
- Primary/blind reconciliation: **202 both accept**, **9 both propose the same target**, **16 propose different targets**, **3 primary-only proposals**, **10 blind-only proposals** (240 total).
- The ledger records each current target and selected target with exact SHA-256, both review alternatives, caller refs/context hash, rationale, confidence, and recomputed placeholder/markup/numeric/protected-literal checks.
- Token preservation passes for all 240 selected targets: 24 placeholder occurrences preserved; 0 markup, numeric, or protected-literal occurrences in source strings; 0 mismatches.
- All **35 carried holds** retain their prior target hashes. All **180 earlier selected-source rows** are preserved and reattested in the candidate-free and primary packets.
- GitHub's exact pinned commit tree matched **34/34** pinned paths: 12 locale catalogs, 20 production caller files, locale runtime, and the committed source-order queue. No source/catalog drift was found.

## Live PR state and refs

The read-only observation before the audit (`2026-11-03T19:36:03.811416+00:00`) and the final observation (`2026-11-03T19:42:42.654393+00:00`) both show PR #204 OPEN/DRAFT at the pinned head/tree. The branch ref and `refs/pull/204/head` both remain `7ca8589266ab4c5a925782a8726d7e57b4ed7427`.

The PR API reports base ref `main` at `2a2b188f10b9460a15bc6d5c34e406b0193d51ba`, while the live `refs/heads/main` is `32c8c40666d93690b8b1847001fd66001a4eaf99`. This base-ref divergence is recorded; the requested PR head, branch, and pull refs stayed pinned. No repository or PR state was changed by this cross-audit.

## Verification

Run from this directory:

```sh
python3 verify_cross_audit.py
```

The verifier checks this packet's `SHA256SUMS.txt`, copied source packet checksums and verifiers, all 240 cell hashes and decisions, token checks, carried holds, source-tree pins, and recorded before/after PR refs. The top-level `SHA256SUMS.txt` is the portable seal; its SHA-256 is included in the handoff.

Original candidate-free, primary, and blind packets are copied under `evidence/` with their original manifests and checksum lists. `external-reference-notes.json` lists lexical references used to corroborate selected terminology.

## Review limits

This is contextual editorial review. No native-speaker attestation is claimed. No tests, builds, CI jobs, workflow changes, or repository/PR modifications were performed.
