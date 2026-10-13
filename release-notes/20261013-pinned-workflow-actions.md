---
category: changed
audience: operators
area: release-pipeline
action: update the repository action allowlist when workflow action revisions change
breaking: false
---
GitHub Actions is enabled for CI and releases with a selected action policy. The allowlist includes only the pinned revisions used by repository workflows and the GitHub-managed CodeQL analyzer; other marketplace actions remain blocked.
