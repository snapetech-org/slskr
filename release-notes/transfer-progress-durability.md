---
category: fixed
audience: users
area: transfers
action: none
breaking: false
---
Transfer progress stays live without forcing synced disk writes for every network chunk. Recovery progress is saved at most once per second per active transfer, while transfer status changes remain immediate.
