---
category: security
audience: operators
area: release
action: none
breaking: false
---
Public release verification permits only HTTPS requests to the configured repository hosts and their explicit artifact mirrors. Every redirect is checked against the same policy, and local files, credentials in URLs, and untrusted destinations are rejected.
