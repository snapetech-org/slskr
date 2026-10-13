---
category: security
audience: operators
area: ci-security
action: none
breaking: false
---

Validation snapshots exclude dotted, extensionless, and suffixed credential environment files, private/API keys, access/refresh-token and client-secret material, and non-source files under credential folders. Source modules and runtime assets in project source trees remain available.
