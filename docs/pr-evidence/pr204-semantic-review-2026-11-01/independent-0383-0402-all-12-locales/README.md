# slskR semantic review: source indices 383–402

This batch covers 20 consecutive source keys and all 240 populated cells across 12 locales. The exact PR #204 review head was `6f8d2b252131a2b68f85d66eb5210e0b6e9f6511` / tree `2fece646fa9dcb6892cad5233b7c79eb08997c24`. Source and caller context is pinned to `7ff454828398de6a3cfb72fe7f0ed21fe419425b` / tree `9e9f2aa743c4ff3236af8f99619803bdc3a37152`.

Exact overlap reconciliation found 132 prior accepted cells, 51 prior correction-needed cells, and 57 fresh cells, with zero exact-status conflicts. Fresh review accepted 45 values and proposed 12 corrections. The candidate set contains all 51 prior correction-needed cells plus the 12 fresh findings. Root independently cross-reviewed all 63 candidates: 38 accepted as proposed, 17 refined, and eight kept unchanged. All 55 approved corrections were applied across 12 locale catalogs. The 177 non-candidate cells with accepted dispositions consist of 132 exact accepted carries and 45 fresh accepted values. The eight unchanged cells are `Auto-Replace (automatic stuck-download replacement)` descriptions. The pinned source tree has no direct literal callsite establishing their display role: six fresh cells remain unreviewed, and two cells with prior exact findings remain correction-needed pending that context.

Candidate ledger SHA-256: `88e51551286eae1f371454f5274ac493fa8938899ddde5347a8fcaeffc6e9433`. Root decision ledger SHA-256: `98db66ed7e1a8154b239c1de69a2ee039c649cb15af69346db3dbb4ed1f969e4`. Exact 63-row apply plan SHA-256: `745dbdbfa8431bacd34cda6a698d5b063aa34ee6419da465e0bf870554eaff19`. Applied-correction ledger SHA-256: `869e95099f0e18fe2b381770729e00f2e62b3b821aa83e39b4065e2afd115af7`. Accepted-cells ledger SHA-256: `0bb84a646a2cecb32b6eeda824e35999321d1d6303ffa11601eccaa1140ab7df`.

Catalog application commit `83aef2e22cede4041943bd0d612357e152e7a9b5` / tree `927bae235b4b57ac51a64389e6becadd75b133c3` is a direct child of the exact review head. Its diff changes only 55 planned target cells in the 12 locale catalogs. The verifier checks every source/current/final hash, all 63 root dispositions, all 55 changed cells, all 177 accepted dispositions, caller file pins, catalog key/population parity (5,437 entries per locale), placeholders, bundle checksums, and `git diff --check`. Native-speaker approval is not claimed.

Headed browser review remains blocked for this exact branch because `web/node_modules` is absent and previewing would require dependency installation or build output. No browser session, desktop, or screenshots were used for this window. Re-capture in the Agentic VM when a no-build preview for the exact branch is available.

No tests, builds, CI, workflow edits, releases, or tags were run. The next contiguous source window is 403–422.

Re-run `verify_candidate_preflight.py` with the prior-audit archive to validate the baseline packet. Run `verify_batch.py` from the repository root to validate the catalog application and evidence bundle:

```sh
python3 docs/pr-evidence/pr204-semantic-review-2026-11-01/independent-0383-0402-all-12-locales/verify_batch.py \
  --repo "$PWD" \
  --prior-audit /path/to/slskr-populated-catalog-review-7ff45482-20261101
```

`SHA256SUMS.txt` covers every file in this completed review bundle except itself. The candidate, root decision, plan, and applied-ledger hashes above independently pin the principal review inputs and outcomes.
