---
category: fixed
audience: users
area: transfers
action: none
breaking: false
---
Resume peer-queued downloads when the uploader reconnects with the matching transfer token. The token from `PeerInit` is used directly, and queued work starts only when a local download slot is available.
