# Localization

The shipped Web UI includes a browser-local interface-language selector for
twelve locales, with English fallback and locale-aware formatting.

## Supported locales

Spanish, Simplified Chinese, Hindi, German, Japanese, French, Brazilian
Portuguese, Arabic, Korean, Traditional Chinese, Vietnamese, and Indonesian.
The rollout order and rationale are documented in the
[localization roadmap](../localization-roadmap.md).

## How it works

- Choose the interface language in **System → Experience Preferences**.
- The preference is stored in the browser, not in daemon-wide settings.
- Missing keys fall back to English.
- Catalog parity and placeholder checks run in the web test suite.
- Dates, times, counts, byte sizes, numbers, track durations, and audio quality
  values use the selected locale's formatting.
- Arabic strings carry local language and direction metadata; app-wide RTL
  layout review is still tracked as remaining work.

## What stays unchanged

Media titles, usernames, filenames and paths, commands, API identifiers,
protocol values, and other user-supplied content are not translated. The
backend returns stable error codes and structured data rather than
pre-localized strings.

## Contributing translations

The catalog translations were machine-generated and still need fluent-speaker
review. The locale catalogs live under the web application; see
[Web UI README](../../web/README.md) for the build, audit, and test workflow.

## See also

- [Localization roadmap](../localization-roadmap.md) for locale coverage and
  remaining work.
- [Web UI and media](web-ui-and-media.md) for the settings surface.
- [Status and support boundaries](../status.md) for maturity notes.
