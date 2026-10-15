---
category: security
audience: operators
area: validation-engine
action: none
breaking: false
---
Validation-run locks now live in the worktree's Git metadata directory instead of shared system temporary storage, preventing other local accounts from pre-creating a lock that blocks validation. If a run is interrupted, remove the stale lock at the path shown in the error after confirming no run remains.
