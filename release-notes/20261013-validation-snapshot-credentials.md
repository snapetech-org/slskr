---
category: security
audience: operators
area: ci-security
action: none
breaking: false
---

Validation snapshots exclude dotted, extensionless, and suffixed credential environment files, private/API keys, access/refresh-token and client-secret material even with source-code extensions, and all files under credential-named folders outside source trees. Other source modules and runtime assets in project source trees remain available.
