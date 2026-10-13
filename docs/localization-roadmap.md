# UI localization roadmap

## Existing support and verified gap

The shipped browser UI is the React application under `web/`. Its reachable branch and available pull-request histories contain no human-language UI catalogs or localization framework. The historical MilkDrop shader translator converts shader code for the WebGL renderer; it is unrelated to interface translation.

## Implementation plan

1. Localize the shipped `web/` application only. Inventory labels, forms, errors, notifications, empty states, and accessibility names; keep the non-shipped dashboard, generated clients, Soulseek usernames, room names, artists, and filenames out of that extraction.
2. Add `i18next` with `react-i18next` and ICU plural support, a central English catalog, English fallback, and a check for missing keys and placeholder parity.
3. Add Display Language to the existing System > Experience settings area. Apply it immediately and save it with the current user's UI preferences, not in a daemon-wide language setting.
4. Format dates, counts, and relative times with the selected locale. Keep API and protocol values stable; the backend should return error codes or structured data rather than strings already localized for one browser.
5. Add locales in the ranked order below. Arabic requires document `lang`/ `dir`, logical CSS properties, and RTL review of search, transfers, chat, settings, and dialogs.

## First-pass locale order

This is a practical rollout order, not a claim about these apps' actual user base. Product-level language analytics are not available. It combines global speaker estimates with online-content usage, and keeps the requested Arabic and Asian-language coverage in the first waves:

1. Spanish (es; es-MX where the product already distinguishes it)
2. Simplified Chinese (zh-Hans / zh-CN)
3. Hindi (hi)
4. German (de)
5. Japanese (ja)
6. French (fr)
7. Brazilian Portuguese (pt-BR)
8. Arabic (ar; requires right-to-left layout support)
9. Korean (ko)
10. Traditional Chinese (zh-Hant / zh-TW)
11. Vietnamese (vi)
12. Indonesian (id)

The World Bank's 2025 report estimates Mandarin Chinese, Hindi, and Spanish at 15%, 7.6%, and 6.9% of the global population respectively; its online-content data also places German, Chinese, and Japanese among the leading languages. [World Bank, Digital Progress and Trends Report 2025](https://documents1.worldbank.org/curated/en/099112525160536089/pdf/P505350-59c98ca8-0803-4f23-b470-17f3dab010ab.pdf). W3Techs tracks website content-language share rather than app users. [W3Techs content-language survey](https://w3techs.com/technologies/cross/content_language%20/ranking). Reorder this list if maintainers later receive reliable demand signals.

## Translation boundaries and acceptance

Translate interface labels, help, empty states, validation, notifications, and errors. Keep media titles, user names, filenames and paths, commands, API identifiers, protocol values, and other user-supplied content unchanged. Use the selected UI language for date, time, number, and plural formatting. Every locale must fall back to English for a missing key; CI should check placeholder parity and report missing strings. Arabic ships only after the app sets `lang` and `dir`, uses logical layout properties, and verifies the core workflows in RTL at narrow and desktop widths.

## Implemented in this PR

System > Experience Preferences now includes a browser-local regional format selector for dates, times, and numbers, covering Spanish, Simplified Chinese, Hindi, German, Japanese, French, Brazilian Portuguese, Arabic, Korean, Traditional Chinese, Vietnamese, and Indonesian. Existing locale-aware date and number output uses that preference. Interface translations and RTL layout remain in the planned catalog rollout.
