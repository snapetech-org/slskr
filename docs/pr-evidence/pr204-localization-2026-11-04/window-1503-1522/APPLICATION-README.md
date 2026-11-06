# Localization review W1503–W1522

This directory retains the complete candidate-free input, primary review, independent clean blind review, and root cross-review packet, with all original checksums intact. The sealed packet contains 60 files. Root cross-review covers 240 cells (20 source positions × 12 locales): 228 accept-current and 12 selected updates (7 corrections, 5 refinements), with no new holds.

The 12 updates were applied in catalog commit `0e793dd5632b3e6d4f25f91fe5b47fc121f3f813` (tree `a7ad6830162f0be4298e2f8c4100e58e2590ccb9`), directly atop reviewed head `a7d00cd97602c5910800330190817fcada008162` (tree `2d0a051348394e809ffc3a1fdbfccd20ba8af283`). `application-readback.jsonl` records all 240 exact catalog values and hashes read from that commit. The portable verifier checks the packet checksums and exact-head readback from the repository root:

```sh
python3 docs/pr-evidence/pr204-localization-2026-11-04/window-1503-1522/verify_window_bundle.py
```

Qualified native-speaker approval is not claimed. No exact-head preview target exists, and the catalog commit has zero deployments; browser acceptance is not claimed. No tests, builds, scans, or CI were run for this window. Workflow files were untouched. The PR remains open and draft; no merge, release, or tag was made.
