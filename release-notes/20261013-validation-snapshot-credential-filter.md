---
category: security
audience: operators
area: validation-security
action: none
breaking: false
---
Trusted validation snapshots now reject camel-case and dot-separated credential filenames and exempt only the known dashboard API keys page, preventing candidate code from reading matching credential files.
