---
category: fixed
audience: operators
area: release-channels
action: none
breaking: false
---
Public package checks now revalidate cached repository responses on each poll,
preventing stale Launchpad metadata from hiding an accepted or published update.
