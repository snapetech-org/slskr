# Root adjudication — W1783–W1802

Root adjudication is pinned to slskR PR #209 input head `0264a4fcaa944fee61049efec0cf3c451416c8b9` / tree `895e57c178d959a23aceddead27623f2dd854ba0`. I reviewed all 56 selected cells against the source text, exact production callers, both independent review rationales, and the selected-target token audit.

The 240-cell ledger records 183 retained current values, 55 corrections, one refinement, and one hold. The 56 selected changes preserve placeholders, markup, numeric values, and protected literals. Korean `1792::ko` stays on hold at its exact current hash pending a qualified locale decision; prior hold `1719::id` remains hash-only and unchanged. No native-speaker approval or headed-browser acceptance is claimed.

`root-selected-targets.jsonl` is the 56-cell exact-hash application plan. `root-overrides.jsonl` is empty because manual adjudication selected the integrated cross-review recommendation for every changed cell and retained the held current text.

The packet-local builder and input packets are in sibling directories. Rebuild the root ledger from a clean worktree at the pinned input head with:

```sh
python3 -B build_root_adjudication.py --repo /path/to/clean-slskR-worktree-at-0264a4f
```

The guarded application and final readback are documented in the sibling `root-application/` packet.
