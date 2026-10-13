---
category: security
audience: operators
area: benchmark-security
action: none
breaking: false
---
The connected-idle runner creates a fresh random status token for each slskR trial and a read-only API key for each slskd trial. It passes credentials through the environment and request headers without saving them in artifacts.
