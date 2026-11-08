---
category: fixed
audience: operators
area: release
action: Check each required publisher and the final completion gate when verifying a release; externally moderated submissions still require approval.
breaking: false
---
Chocolatey publication is part of the tagged release workflow and is required before Discord announces completion. Missing credentials fail publication. Winget recovery creates only the release manifest branch, verifies an existing matching submission, and preserves published fork history. Pending legacy Windows packages declare their Visual C++ runtime prerequisite.
