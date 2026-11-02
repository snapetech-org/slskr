# slskR PR #204 W703–722 primary review

- Exact PR head/tree: `8b2f1f5fb216fb9946e823c5dff86d5e76a30b84` / `90225bd501256ac84c520105e714df9fc9d6aefc`.
- Reviewed source positions 703–722: 20 IDs × 12 locales = 240 cells.
- Primary decisions: 160 accept-current, 67 correction proposals, 13 holds.
- The Arabic `Cleared {count} searches` value is preserved as a six-category ICU plural map pending native plural review. All 12 `Click to load native Soulseek interests for` values are held because the caller concatenates a username after the localized fragment, preventing natural word order in several locales.
- All proposals preserve source placeholders and protected product names. Cross-review and qualified native-speaker review remain required.
- Composite plural-map hashes use SHA-256 over compact UTF-8 JSON with sorted category keys; string targets hash raw UTF-8. This keeps the Arabic six-category object reproducible.
- No repository or PR changes, tests, builds, scans, CI, workflows, browser review, releases, tags, or merges.
