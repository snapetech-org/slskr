---
category: security
audience: operators
area: ci-security
action: none
breaking: false
---
Pull request validation uses hosted runners, leaving the persistent Linux runner for trusted main pushes and manual runs. Local jobs protect GitHub command files, cap Cargo builds at one job, and stream private logs within a 16 MiB limit. Rust receipts are stored per workflow attempt; reconciliation uses each runner's newest result and rejects duplicates.
