---
category: security
audience: operators
area: ci-security
action: none
breaking: false
---
Pull request validation runs on GitHub-hosted runners; the persistent Linux runner is reserved for trusted main-branch pushes and manual runs on main. Local jobs protect GitHub command files before running repository scripts and keep Cargo builds at one job. Validation task logs are streamed to private, size-limited files and retained after failures. Rust receipt artifacts are separated by workflow attempt, and reconciliation selects the newest receipt for each runner while rejecting duplicate receipts from the same attempt.
