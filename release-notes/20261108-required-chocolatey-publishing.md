---
category: fixed
audience: operators
area: release
action: Require Chocolatey publication before announcing or completing a full release.
breaking: false
---
Chocolatey is part of the tagged release job graph. Its publication result gates Discord and the final completion check, and missing credentials fail instead of producing a successful no-op. Trusted tag calls and manual main-branch recovery use explicit, tested guards.
