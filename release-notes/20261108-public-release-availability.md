---
category: fixed
audience: operators
area: release
action: Retry failed public availability verification after external repositories publish their packages.
breaking: false
---
Release announcements require public COPR and Launchpad binaries, merged Winget manifests, and Chocolatey approval. An explicit owner-authorized first-review exception retains the prepared Chocolatey package without uploading and records it as pending rather than published.
