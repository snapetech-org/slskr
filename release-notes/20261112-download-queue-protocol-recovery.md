---
category: fixed
audience: users, operators
area: transfers
action: none
breaking: false
---
Downloads now use Soulseek's `QueueUpload` negotiation and accept the matching peer's inbound offer. After reconnect, slskR re-requests remote-queued downloads so a lost peer session does not leave them queued indefinitely.
