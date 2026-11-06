# slskR PR #209 W1543–W1562 application evidence

The product commit applies exactly the 27 correction rows in the sealed cross-review ledger. Its parent is the reviewed input head c15eddffec2c4c24cc091b2a6ebf0c43fa58ef1b. It changes 27 catalog value tokens across 11 locale catalogs. The remaining 208 accepted cells and all 5 held cells retain their current values and SHA-256 hashes.

The full 240-cell readback is in apply-readback-cells.jsonl. exact-hash-apply-plan.json records each selected target with its currentTargetSha256 guard and selected target hash; accepted and held cells are recorded hash-only in the plan. postimage-catalog-pins.json contains all 12 final catalog file hashes, Git blobs, byte counts, key counts, and ordered-key hashes. The catalogs keep their original 5,441-key order.

cross-review/ is an exact copy of the sealed cross-review packet. review-inputs/ contains exact copies of the candidate-free, primary, and independent blind packets referenced by that review. The top-level verifier checks every copied packet checksum and reconciles the plan and readback with the product commit and all 240 cross-review cells.

The PR body update is recorded in pr-before.json, pr-after.json, pr-before-body.txt, pr-after-body.txt, pr-body-summary.md, and pr-body-update-attestation.json. The attestation confirms the old body is an exact prefix of the updated body and the API readback matched.

Run python3 verify-application.py from this directory. The product catalog commit is separate from this documentation and evidence commit. No tests, builds, scans, CI, workflow edits, merge, release, or tag were performed. No native-speaker sign-off or browser review was performed.
