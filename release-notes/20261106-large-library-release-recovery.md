---
category: fixed
audience: operators
area: shares
action: Upgrade and rescan shares; retain an explicit scan_max_files setting appropriate for the library.
breaking: false
---

Completed share scans now publish one shared immutable index instead of duplicating the entire index on an asynchronous runtime worker. This reduces peak memory and runtime stalls for large NAS libraries while preserving the last complete index after failed or capped scans. This release also includes bounded session-command admission and server writes, reviewed localization corrections, dependency security updates, and restored native GitHub-hosted CI and release publishing.
