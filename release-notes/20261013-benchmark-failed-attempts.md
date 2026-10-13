---
category: changed
audience: operators
area: benchmarks
action: none
breaking: false
---
The idle comparison runner records each started trial with its profile, repetition, timestamps, and failure reason before stopping after a login, API, or cgroup-read error. Completed measurements remain separate from failed attempts in the raw artifact.
