---
category: changed
audience: operators
area: release-pipeline
action: update the repository action allowlist when workflow action revisions change
breaking: false
---
GitHub Actions is enabled for CI and releases with a selected action policy. GitHub-owned actions are allowed, while third-party marketplace actions are limited to the pinned revisions used by repository workflows; other third-party actions remain blocked.
