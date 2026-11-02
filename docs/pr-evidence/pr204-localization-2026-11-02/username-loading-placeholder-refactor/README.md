# slskR PR #204 username-loading placeholder refactor

At input head `783201d6541188ce7af5b2e5dd5572eb919e8d10` / tree `5cb1b2b5699336a0ca7a966391eea12a1d553017`, independent review confirmed 12 locale targets for the complete username sentence. Eleven were accepted and the Japanese wording was refined; every target has one `{username}` placeholder and preserves `Soulseek`.

The popup starts the fetch when it opens, so the old “Click to load” copy was misleading. The sentence `Loading native Soulseek interests for {username}.` now appears in the active loading branch with the spinner. The username is wrapped in FSI/PDI only for display; the raw value remains in API calls and identity comparisons. The popup is omitted when there is no username, and the obsolete idle fragment returns no text.

All 12 locale catalogs replace the old loading/fragment IDs with the reviewed placeholder source and retain identical 5,440-key sets. The exact source-code/cell apply plan and readback are included with the independent code and locale review. Native-speaker review and current-head browser review remain outstanding. The popup transition may show a brief blank frame depending on UI batching; no settled empty state remains for a valid username.

No tests, builds, scans, CI, workflow changes, releases, tags, or merges were performed for this change.
