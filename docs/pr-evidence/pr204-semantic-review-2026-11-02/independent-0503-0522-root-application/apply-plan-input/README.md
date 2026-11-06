# slskR PR #204 W503–522 exact-hash apply plan

Read-only plan pinned to PR head `7bf9f91c0f34269434fee70cd2f7067afeaf6122` (`b598a6ad004a504037e64ebf541b5c9e01d54765` tree). It covers 240 cells: 49 planned target updates (29 primary proposals accepted, 10 refined primary proposals, 10 independent misses) and 191 cells with no target change (155 accepted current targets, 12 prior-routed holds, 24 no-op cells).

`source-current-final-plan.jsonl` contains every cell and pins source, current target, and planned final target text and SHA-256. `planned-target-updates.jsonl` contains the 49 proposed changes. The 12 prior-routed rows are copied byte-for-byte to `prior-routed-unchanged.jsonl`; each hold and no-op final value/hash equals its exact current target.

Plan validation re-read exact PR catalog blobs and verified all 240 current hashes, the PR branch/head/tree, and prior-routed provenance bytes. The plan is not applied. Native-speaker review remains required before applying candidate targets.
