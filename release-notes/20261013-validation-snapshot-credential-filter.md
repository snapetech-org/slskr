---
category: security
audience: operators
area: validation-security
action: none
breaking: false
---
Validation snapshots exclude qualified credential filenames and directories, including source-like files, while preserving unrelated auth names such as `peer_authentication.rs` and `*-controller-auth-policy.json`. Descriptive Markdown under `docs/` and `release-notes/` stays available; credential configuration files remain excluded. Source modules and service dirs remain accessible.
