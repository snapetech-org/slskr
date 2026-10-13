---
category: security
audience: operators
area: validation-security
action: none
breaking: false
---
Trusted validation snapshots now reject camel-case and dot-separated credential filenames plus qualified credential directories outside source trees. Only the known dashboard API keys page is exempt, preventing candidate code from reading matching credential files.
