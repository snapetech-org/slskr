# W1423–W1442 application evidence

This application is pinned to PR #204 head `7ca8589266ab4c5a925782a8726d7e57b4ed7427` and tree `09adcb271a2eb92770df4a20098dccc3fde2a59f`. It applies the sealed cross-audit’s **39 exact-hash updates** (38 corrections and 1 refinement), retains 201 current values, opens no new holds, and preserves all 35 carried holds and 180 earlier selected-source reattestations.

`before-catalogs/` contains the byte-identical baseline catalogs. `apply-plan.jsonl` lists only selected changes; `application-readback.jsonl` covers all 240 cells; `catalog-invariants.json` records all 12 catalog key counts, key order, before/after hashes, and changed source keys; the two prior-state readbacks record carried holds and selected-source lineage.

The portable verifier checks the embedded packet checksums and verifiers, exact 240-cell readback, selected hashes, token and protected-literal preservation, exact changed-value set, key order, carried holds, earlier selections, and absence of workflow changes. Run from the repository root:

```sh
python3 docs/pr-evidence/pr204-localization-2026-11-03/window-1423-1442/application/verify_application.py
```

This is contextual machine-assisted editorial review; qualified native-speaker review was not performed. No tests, builds, scans, CI dispatches, workflow edits, merges, releases, or tags were performed for this window.
