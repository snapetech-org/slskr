# Application record

The user authorized translation and review completion, commits, pushes, and PR updates. This plan applies only the 58 cross-audited `correction` and `refinement` cells. It retains every accepted current value and all 23 carry-forward holds. No test, build, scan, CI, workflow, merge, release, or tag action is included.

`apply_exact_head.py` refuses a stale head/tree, unexpected worktree changes, target value/hash drift, catalog shape drift, missing prior holds, or selected-target hash mismatch. It records the preflight, applies the exact plan, and reads back all 240 reviewed cells.

Run `python3 verify_application.py` from this directory after application; run `python3 ../verify_window_bundle.py` for the portable whole-window check.
