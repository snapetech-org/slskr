# UI localization roadmap

## Existing support and verified gap

The shipped browser UI is the React application under `web/`. Its reachable branch and available pull-request histories contain no human-language UI catalogs or localization framework. The historical MilkDrop shader translator converts shader code for the WebGL renderer; it is unrelated to interface translation.

## Implementation plan

1. Localize the shipped `web/` application only. Inventory labels, forms, errors, notifications, empty states, and accessibility names; keep the non-shipped dashboard, generated clients, Soulseek usernames, room names, artists, and filenames out of that extraction.
2. Extend the compact shell catalog with screen-sized batches and English per-key fallback. Add a full message framework when dynamic errors or plural rules make it useful, with missing-key and placeholder checks.
3. Add Display Language to the existing System > Experience settings area. Apply it immediately and save it in this browser rather than in daemon-wide settings.
4. Format dates, counts, and relative times with the selected locale. Keep API and protocol values stable; the backend should return error codes or structured data rather than strings already localized for one browser.
5. Add locales in the ranked order below. Arabic requires document `lang`/ `dir`, logical CSS properties, and RTL review of search, transfers, chat, settings, and dialogs.

## First-pass locale order

This is a practical rollout order, not a claim about this app's actual user base. Product-level language analytics are not available. It combines global speaker estimates with online-content usage and includes the requested Asian-language and Arabic coverage:

1. Spanish (es; es-MX where the product already distinguishes it)
2. Simplified Chinese (zh-Hans / zh-CN)
3. Hindi (hi)
4. German (de)
5. Japanese (ja)
6. French (fr)
7. Brazilian Portuguese (pt-BR)
8. Arabic (ar)
9. Korean (ko)
10. Traditional Chinese (zh-Hant / zh-TW)
11. Vietnamese (vi)
12. Indonesian (id)

The World Bank's 2025 report estimates Mandarin Chinese, Hindi, and Spanish at 15%, 7.6%, and 6.9% of the global population respectively; its online-content data also places German, Chinese, and Japanese among the leading languages. [World Bank, Digital Progress and Trends Report 2025](https://documents1.worldbank.org/curated/en/099112525160536089/pdf/P505350-59c98ca8-0803-4f23-b470-17f3dab010ab.pdf). W3Techs tracks website content-language share rather than app users. [W3Techs content-language survey](https://w3techs.com/technologies/cross/content_language%20/ranking). Reorder this list if maintainers later receive reliable demand signals.

## Translation boundaries and acceptance

Translate interface labels, help, empty states, validation, notifications, and errors. Keep media titles, user names, filenames and paths, commands, API identifiers, protocol values, and other user-supplied content unchanged. Use the selected UI language for date, time, number, and plural formatting. Every locale must fall back to English for a missing key; CI should check placeholder parity and report missing strings. Arabic translated labels use local `lang` and `dir` metadata. App-wide RTL still requires logical layout properties and review of core workflows at narrow and desktop widths.

## Implemented in this PR

System > Experience Preferences offers a browser-local interface-language selector for twelve first-wave locales. The shipped Web UI now localizes 3,852 source strings across browsing, search, chat, rooms, collections, player, wishlist, transfers, and system screens, including app-owned statuses, messages, and accessibility labels. The catalog audit covered 46,224 locale cells with no missing translations or placeholder mismatches. Media and user-provided content, paths, and raw API/protocol values remain unchanged.

The regional-format preference also localizes digits in track durations and audio quality values, alongside the existing dates, counts, transfer sizes, and metric/network values. Arabic strings carry local language and direction metadata.

Regional formatting uses the selected preference for dates, times, counts, byte sizes, and numbers in the shipped UI. Changes re-render open screens immediately, keep working in the current tab when browser storage is blocked, and update from another tab's preference changes.

## Remaining work

The catalog translations were machine-generated and still need fluent-speaker review. Review the full Arabic layout interactively at narrow and desktop widths before claiming app-wide RTL support.
