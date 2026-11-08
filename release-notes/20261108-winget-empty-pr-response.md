---
category: fixed
audience: operators
area: release-channels
action: none
breaking: false
---
Winget publication now handles an empty GitHub pull-request response correctly
instead of treating it as a closed request. The regression fixture reproduces
PowerShell's actual REST array behavior while preserving existing-PR checks.
