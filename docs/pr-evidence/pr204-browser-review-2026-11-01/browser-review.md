# slskR PR #204 headed localization review

- Initial review code head: `223aac4ddb24ec869d15a4078c66d8037cd7f9dc`
- Follow-up code head: `8deec4a0a4f88430005f221cc6598ad34f0002b3`
- Route: `/system/experience` in the native runtime profile
- Browser: isolated headed Chrome in the persistent Agentic VM, 1440 × 1000
- Preview: task-local Vite server with a synthetic local session and mocked API/Hub; no production account or external integrations were used
- Locales visited: `es`, `zh-Hans`, `hi`, `de`, `ja`, `fr`, `pt-BR`, `ar`, `ko`, `zh-Hant`, `vi`, `id`

The review covered primary navigation, the Advanced → Experience settings page, Search/Player/Messages preferences, the interface-language selector, regional-format selector, persistent audio player controls, and footer status labels. Arabic was visually checked in RTL; the settings cards, selector, and player artwork/control layout flowed right to left. No obvious clipping or overlap appeared at this desktop viewport. This was not a mobile review or native-speaker signoff.

## Findings for correction

- `Scrobble Mode` is mistranslated in Spanish as “Modo de exploración”; Simplified and Traditional Chinese render it as “拼字游戏模式” / “拼字遊戲模式” (Scrabble game). Korean's visible label says scrobble but the preference's accessible name says “scroll mode.” Review all locale variants for a consistent music-listening-history meaning.
- `Capture local history` is rendered as geographic/local-area history in the observed locales. In this Player section it means browser-local playback/listening history.
- `Player radio seed preference` uses the gamer/player sense in multiple locales despite the section being the audio player; review it with the product's audio-player term.
- The Automation & Jobs navigation label uses the employment sense in Spanish, Brazilian Portuguese, Hindi, Vietnamese, and Indonesian; review it in the scheduled-task sense.
- The first pass found `Use browser settings` in English in the regional-format selector. The follow-up localizes the system option using the selected interface language. An independent review accepted all 12 locale values at high confidence in this dropdown context; exact-cell records are in `docs/localization/pr204-regional-format-key-review-2026-11-01.json` (SHA-256 `69738b673bd97016f9783c9be6f35041a0000335e95aa6c19eb64f266f33cd86`).

The scrobble, local-history, radio-seed, and scheduled-jobs findings are still being reconciled against exact cell hashes and the pinned semantic review. The original 12 screenshots record the first headed pass. `id-followup-8deec4a0.png` records the localized regional-format option on the follow-up head; the full 12-locale screenshot set will be refreshed after the remaining catalog corrections.

## Screenshots

One screenshot per direct locale is retained in this directory. `SHA256SUMS` records their hashes.
