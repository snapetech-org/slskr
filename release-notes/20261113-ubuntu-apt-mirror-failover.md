---
category: fixed
audience: operators
area: packaging
action: none
breaking: false
---
Build jobs try Ubuntu's canonical archive, security, and ARM endpoints before independent mirror fallbacks. If every mirror fails to refresh an index, package installation stops instead of using stale index data.
