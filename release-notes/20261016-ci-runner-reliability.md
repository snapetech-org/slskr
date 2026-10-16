---
category: fixed
audience: operators
area: release-pipeline
action: none
breaking: false
---
Release builds use GitHub-hosted runners, keep caches within each workflow job, and sync Winget manifests through the canonical organization fork. The former self-hosted cache fallback is no longer used.
