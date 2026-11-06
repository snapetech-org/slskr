# Guarded application and readback — W1783–W1802

Product commit `fe1d95c89a1ebab79625299732c09d3649ee20e4` / tree `63b34b52b0165db534cd7a4e2b06ba277f1309ae` applies the 56 targets in the sibling root adjudication plan across the 12 locale catalogs.

`preflight.json` records exact-hash validation against input head `0264a4fcaa944fee61049efec0cf3c451416c8b9` / tree `895e57c178d959a23aceddead27623f2dd854ba0`. `product-pin.json` pins the catalog product commit and all 12 resulting catalog file hashes. `final-head-readback.jsonl` and `application-summary.json` record the post-commit verification: all 240 reviewed values match, all catalogs retain 5,441 ordered keys, and only the selected 56 values changed. The Korean hold and 183 accepted current values remain unchanged.

To replay application in a clean worktree at the input head, run `--preflight`, then `--apply`, commit only the planned catalogs, update `product-pin.json` to that product commit, and run `--verify-after`. The current committed product pin has already passed `--verify-after` against the product commit. No repository tests, builds, scans, CI, or workflows were run or changed for this window.
