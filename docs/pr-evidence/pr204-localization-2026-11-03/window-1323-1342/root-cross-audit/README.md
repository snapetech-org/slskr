# slskR PR #204 W1323-W1342 root cross-audit

## Exact pins and evidence

Live PR #204 was reattested OPEN/DRAFT on branch codex/slskr-l10n-audit-20261030 at head 6ccefe07d8154acbc08e34249ef7039dc5bc1f08, tree e0c1d1341be45ed73bd30cf027b479ce3b5bb95d. Both the remote branch ref and pull ref matched the head.

The candidate-free input, primary review-v2, and independent blind review were checksum-verified and their own verifiers passed before reconciliation. Their exact paths and checksum-list hashes are recorded in summary.json and verification.json. Every current cell was matched to source key, production caller context, source/target hashes, locale, and placeholder/markup/numeric/protected-literal checks.

## Reconciliation

The root ledger covers all 240 cells. The primary reviewed 40 proposal cells, 199 retains, and one semantic hold; the blind reviewer proposed 20 corrections and 4 refinements. Ten changes were exact proposal agreement, 19 were primary-only, 3 were blind-only, and 11 had different proposed targets. All 34 cells requiring explicit reconciliation are in disagreement-resolutions.jsonl.

The proposal-only apply plan selects 43 cell changes, retains 196 current cells, and holds one current-window cell. The Vietnamese position 1335 federation wording remains held because the exact technical term is unresolved in the pinned locale context. No callerless cells occur in this window.

The primary reviewer found two zero-width spaces in Korean position 1327. Independent code-point inspection of all 240 current target strings found those as the only format-control characters; the selected proposal removes them.

Where terminology conflicts arose, the cross-audit uses pinned catalog terms such as Player, Rooms, and Artist Release Radar, with exact references copied into terminology-evidence.jsonl. Japanese auto-fill wording uses automatic queue replenishment rather than automatic input. All selected targets preserve source placeholders and protected literals.

The separate 22 carry-forward holds are copied byte-for-byte and reattest unchanged: 12 Ecosystem cells at position 1257 and 10 W1303 holds at positions 1310, 1311, 1313, and 1316.

## Scope

proposal-only apply plan; it is not application authorization. No repository or PR metadata was changed. No tests, builds, or CI were run.

Run python3 verify-root-crossaudit.py and sha256sum -c SHA256SUMS.txt from this directory.
