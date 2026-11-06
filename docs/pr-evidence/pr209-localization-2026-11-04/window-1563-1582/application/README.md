# slskR PR #209 W1563–W1582 application evidence

The product commit `62e74939e7b8145055dbd77d83d2b5c3804d3b0b` applies exactly 18 guarded localization value changes (16 corrections and 2 refinements) across all 12 locale catalogs. Its parent is the reviewed input head `f42c7e4be1f2bc9d63e13607d3c311d37f83f355`. The three values at W1569 Hindi, W1570 Hindi, and W1570 Spanish follow the separate root-adjudication packet. The remaining 222 cross-review accept-current cells retain their exact current-target hashes; there are no holds.

The full 240-cell catalog readback is in `apply-readback-cells.jsonl`. `exact-hash-apply-plan.json` records each selected target with its `currentTargetSha256` guard and the 222 accepted cells hash-only. `postimage-catalog-pins.json` records all 12 final catalog hashes, Git blobs, byte counts, key counts, and ordered-key hashes. The catalogs keep their original 5,441-key order.

`cross-review/` is an exact copy of the sealed cross-review packet. `review-inputs/` contains exact copies of the candidate-free input, primary review, independent blind review, and separate root-adjudication packet. The top-level verifier checks every copied packet checksum and reconciles the plan/readback against the product commit and all 240 cross-review cells.

The PR body update is recorded in `pr-before.json`, `pr-after.json`, `pr-before-body.txt`, `pr-after-body.txt`, `pr-body-summary.md`, and `pr-body-update-attestation.json`. The attestation confirms the original body is an exact prefix of the updated body and the GitHub API readback matched. That body update was read back while the PR head was the product commit; the evidence commit is a separate subsequent commit.

Run `python3 verify-application.py` from this directory to verify the nested packets, exact catalog changes, readback, body prefix, and commits. The product catalog commit is separate from this evidence commit. No tests, builds, scans, CI, workflow edits, merge, release, or tag were performed. The pre-commit hook was skipped because it launches a local Semgrep scan, which the task explicitly prohibited. No native-speaker sign-off or browser review was performed.
