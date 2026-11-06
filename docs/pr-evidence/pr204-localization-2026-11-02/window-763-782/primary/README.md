# slskR PR #204 W763–782 primary review

- Exact live PR head/tree: 32903976fabe543f89dd5950245ba11dd77c8eb3 / ebf75888b3087e83fe2327495c17611802925f71 (OPEN, DRAFT).
- Reviewed frozen source positions 763–782: 20 source IDs × 12 locales = 240 cells.
- Primary decisions: 197 accept-current, 43 correction proposals, zero holds.
- Prior populated-catalog review status was 105 accepted, 15 correction-needed, and 120 not-reviewed. All 240 source/current-target hashes were reattested. Only the 120 accepted/correction-needed dispositions were reused; the 120 not-reviewed cells were reviewed fresh, without adopting old machine suggestions.
- The 43 proposals are 15 reattested prior corrections plus 28 fresh corrections. They address collection-share vs sharing terminology, Chinese collection/favorite false friends, the Comments counter delimiter, Compact mode wording, pinned-node comparison, and Vietnamese perceptual-hash terminology.
- Every source has a direct caller except “Collections — full sets and 1G1R.” That string was reviewed standalone only; all locales preserve exact 1G1R and convey the full-set category.
- Exact protected literal 1G1R is retained in all 12 locales. ContentID and Levenshtein were reviewed as technical names: some catalog targets localize ContentID as “content identifier,” Japanese transliterates Levenshtein, and the fresh Vietnamese/Korean/Chinese candidates retain the named terms. Placeholders, punctuation, and the ASCII opening parenthesis required by the caller were checked.
- Caller lines are pinned with exact line/file hashes and blobs. The exact-head repo evidence search found no applied decisions for these 20 source IDs; scratch search found no pre-existing W763 packet before this one.
- The frozen inventory has 5,437 source keys; each live locale has seven extra catalog keys and four inventory keys absent. See manifest.json for exact deltas.
- Indexes 762 and 763 are adjacent; all 12 index-762 targets match the W743–762 packet. This window does not overlap W703–722, W723–742, or W743–762; index 783 is “Complete.”
- No repository or PR changes, tests, builds, scans, CI, browser work, workflows, releases, tags, or merges.
