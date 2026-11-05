# Root adjudication — W1763–W1782

Root adjudication reconciles the sealed 240-cell cross ledger with exact source, current-target, selected-target, and caller-context hashes at input head `5191888071f54061a6012acdedfeb518a6cb3661` / tree `d5728c24b54a06dda432afd2ef5f378206a6cb8f`.

The root retained 131 current values, selected 105 corrections, and selected 4 refinements. An independent post-cross audit checked all 109 selected values and found no issue or required override. The prior hash-only hold `1719::id` remains separately attested and unchanged.

`build_root_adjudication.py` records the 240-cell ledger, exact-hash selection plan, summary, and input attestation. Re-run it from a clean worktree at the pinned input head with:

```sh
python3 -B build_root_adjudication.py --repo /path/to/slskR
```

The guarded catalog application and full 240-cell post-commit readback are in the sibling `root-application/` directory.
