# slskR PR #204 Lidarr “Not configured” primary review

This separate 12-cell review covers the existing Lidarr status literal `Not configured`, which is not present in any of the twelve locale catalogs at pinned PR #204 head `3a4c26a7faf1dacbd8f3a382d47243b7063a262d` / tree `9059d27001d306ea6b064560137ff2a51dd19021`. The source caller is the API-key status branch in `web/src/components/System/Integrations/LidarrPanel.jsx`; the adjacent label is `API Key`.

The packet proposes a locale-specific status for each direct locale. It is primary machine-assisted review and remains unapproved until a different reviewer reattests the exact missing key at the then-current PR head and independently checks the wording. Do not apply this packet without that cross-review.

The local branch head remains pinned to the PR base, with W803–W822 catalog and caller changes uncommitted in the worktree. No tests, builds, CI, browser actions, or PR writes were performed.
