# slskR PR #204 localization review and application: W1463–W1482

This evidence directory contains the exact-head candidate-free source/caller packet, primary review, clean independent blind review, cross-audit, application plan, hash-only readback, and commit attestations for positions 1463–1482 across 12 locales.

## Results

- Cross-audit: 169 accept-current, 29 corrections, 30 refinements, and 12 hash-only holds at position 1466, which has no exact production caller.
- The primary review supplied 44 proposals and the clean independent review supplied 51. The cross-audit reconciled 21 identical proposals, 15 competing targets, 8 primary-only proposals, and 15 independent-only proposals.
- Sixteen FTP protected-literal gaps are corrected with exact pinned FTP caller context. Twelve FAIL gaps remain hash-only holds.
- The pre-existing local catalog commit `6cf5a622ba90a4f9695bcb85728db094b566f106`, parented on reviewed PR head `2db7fa06845d9d94a5e5da2ddb5ecfdc04100ade`, changes 59 values across 12 locale catalogs. All 240 reviewed cells were read back by hash; 65,233 other or retained values are unchanged.
- Prior selection, hold, and source-order lineage continuity is represented only by counts, byte counts, and SHA-256 hashes. The three raw continuity/lineage files are omitted from this evidence copy; their original names, hashes, and byte counts remain in the sealed candidate-free manifest/checksum list and hash-only summary. The canonical task-scratch packet remains the source of those sealed files.

## Verify

Run from this directory:

    python3 verify_window_bundle.py
    sha256sum -c SHA256SUMS.txt

The root verifier checks the root inventory/checksums, then runs the hash-only candidate-free verifier, primary verifier, clean independent blind verifier, cross-audit verifier, and application verifier. It never decodes or parses the omitted raw continuity/lineage files. The original candidate-free verifier is retained as packet provenance but is not invoked because it expects those withheld raw files.

## Scope

No PR push/update, workflow edit, test, build, CI dispatch, scan, deployment, merge, release, or browser action was performed by this evidence integration. The evidence commit is separate from the catalog commit; the catalog commit itself remains local and unpushed.
