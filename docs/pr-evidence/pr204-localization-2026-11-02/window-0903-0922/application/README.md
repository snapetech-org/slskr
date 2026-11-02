# slskR PR #204 W903–W922 application

Application input was PR head `b1e814ef11d55fd1710d0e2522df14fee9ff0a70` / tree `50fef41fa1abcfcceb9a99cfd756ae014e51e286`. The exact-hash applier verifies the sealed primary and independent packets, all 240 current target hashes, source IDs, placeholders, markup, protected `URL`, and Arabic plural categories before writing the 42 independently accepted values.

`exact-hash-apply-plan.jsonl` contains the 42 changed cells; `full-window-apply-plan.jsonl` records all 240 decisions. `catalog-preapply-pins.jsonl`, `full-window-readback.jsonl`, and `catalog-postapply-attestation.json` record exact before/after values and catalog key order. `apply-summary.json` records the resulting counts. The seven-PR live snapshot captures the branch state immediately before application.

Run `python3 apply-reviewed-window.py` from the repository at the pinned pre-apply head to reproduce the application. The script rejects any head, tree, packet, catalog, source, or target hash drift.
