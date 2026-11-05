# Guarded exact-hash application

`apply_root_application.py` verifies the 240-cell root ledger and 109-cell plan against the pinned input head/tree and all 12 canonical catalogs before it writes anything.

The recorded preflight and application used the clean worktree at `5191888071f54061a6012acdedfeb518a6cb3661`. After the focused catalog commit, `product-pin.json` recorded product commit `f96dfbda509d397af97a09c29f2398e6020fd06d`, tree `70d0bd6bf34d7ffeb8020eb3ee773b55e4e91747`, and the final catalog hashes. `--verify-after` then read back all 240 cells and confirmed all 12 complete files match the pinned product commit.

For a replay from the exact input head, pass the repository worktree explicitly:

```sh
python3 -B apply_root_application.py --repo /path/to/slskR --preflight
python3 -B apply_root_application.py --repo /path/to/slskR --apply
```

After committing the catalog milestone and recording its product pin, run:

```sh
python3 -B apply_root_application.py --repo /path/to/slskR --verify-after
```
