# slskR PR #204 W843–W862 third-party adjudication

This packet adjudicates the 13 new correction proposals and one revised French primary proposal from the exact-head primary, main cross-review, and Hindi/Indonesian/Vietnamese subset packets. PR #204 was OPEN/DRAFT at `b52b7c9abd112328a70d9e811d3b6aa2d4feb8e6`, tree `d7a46bce75c76e3a74736b85175f7fa412324f39`. All seven localization PR API heads, refs, and HTTPS branch heads agreed at start and final reattestation.

## Decisions

All 14 proposals are accepted. The 13 new corrections are W842 zh-Hans/zh-Hant, W842 Vietnamese, W843 French/Hindi, W849 ar/de/es/fr/ja/zh-Hans/zh-Hant, and W859 Hindi. The revised primary proposal is W852 French. No holds remain.

The count-label punctuation follows the pinned caller, which appends ASCII `)` after the localized prefix. W843 terminology follows the product context: the Vietnamese target corrects “customers” to software clients; the French plural “hachages” matches hash-value terminology; Hindi retains exact `slskr` and the established “क्लाइंट” term. W849 proposals mark the live-search connection as in progress, matching the loading icon in the caller. W852 French describes the numeric connection wait limit in milliseconds. W859 Hindi uses “सहमति” for agreement rather than unanimity; neighboring consensus labels use some other Hindi variants, noted for later terminology harmonization.

## Reattestation and limits

All 12 locale catalog blobs and file hashes were checked at the exact PR head. The 14 current cells and five distinct caller contexts were re-read from the clean exact-head worktree and hashed. Placeholder, markup, and protected `slskr` checks pass for all 14 targets. Input packet SHA256SUMS files were verified.

This is moderate-confidence static machine-assisted adjudication, not native-speaker or headed-browser approval. No repository/PR changes, tests, builds, CI, or browser work occurred.

`adjudication-ledger.jsonl` contains per-cell current/proposed/final hashes, caller pins, rationale, and integrity checks. `terminology-references.jsonl` records related current catalog terminology and values. `all-seven-pr-heads-start.json` and `all-seven-pr-heads-final.json` preserve the live head checks. `SHA256SUMS` covers the complete packet.
