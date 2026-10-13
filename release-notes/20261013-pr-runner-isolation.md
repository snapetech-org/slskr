---
category: security
audience: operators
area: ci-security
action: none
breaking: false
---
Pull requests use hosted runners; the persistent Linux runner is reserved for trusted main pushes and manual runs. Local jobs protect command files, cap Cargo at one job, enforce memory and swap limits, and retain private streamed logs (16 MiB). Rust receipts are stored per attempt and reconciled using each runner's newest result. The guide documents sandbox mounts and retry checks.
