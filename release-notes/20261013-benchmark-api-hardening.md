---
category: security
audience: operators
area: benchmark-security
action: none
breaking: false
---
The idle benchmark runner restricts local status requests to fixed loopback HTTP endpoints and limits JSON response bodies to 64 KiB, preventing file-scheme reads and oversized status payloads.
