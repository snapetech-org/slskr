# slskR PR #204 W723–742 exact-hash review and application

Primary review and independent cross-review covered 20 source strings × 12 direct locales (240 cells) at input head `32903976fabe543f89dd5950245ba11dd77c8eb3` / tree `ebf75888b3087e83fe2327495c17611802925f71`. The independent review reattested 49 caller references across 13 files with zero mismatches and rechecked adjacent W722 evidence.

Final dispositions: 145 accept-current, 43 corrections, 3 refinements, and 49 holds. Applied 46 exact-hash target changes across all 12 locale catalogs. Each catalog retains 5,440 keys. All 240 final values match the cross-reviewed ledger; placeholder, markup, and protected-literal mismatch counts are zero.

The 49 holds comprise 36 cells with no direct caller, 12 W741 cells whose “leaving anything” wording does not describe the actual local panel-close handler, and one Vietnamese W724 cell held for fluent terminology review. The panel-close handler filters local UI state and does not delete a thread or leave a room/channel.

The complete primary and independent cross-review packets, apply plan, exact readback, and checksums are retained here. This window has no post-apply headed-browser review; qualified native-speaker approval remains outstanding. A preliminary catalog-wide audit mislabeled 15 Arabic ICU plural-form objects as blank because their JSON values are category maps rather than strings. They were not altered by this window; exact category and placeholder validation is in progress. The commit-time Semgrep Community Edition hook scanned one staged evidence-builder Python file with `p/default` (290 rules; zero findings); it did not scan product source. No tests, builds, CI, workflow changes, releases, tags, or merges were performed.
