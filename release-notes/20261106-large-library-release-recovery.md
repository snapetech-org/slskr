---
category: fixed
audience: operators
area: shares
action: Upgrade and rescan shares; retain an explicit scan_max_files setting appropriate for the library.
breaking: false
---

Large-library share scans publish one shared immutable index, reducing peak memory and runtime stalls while preserving the last complete index after failures. Includes bounded session queues and server writes, localization corrections, dependency security updates, and restored GitHub-hosted CI and publishing.
