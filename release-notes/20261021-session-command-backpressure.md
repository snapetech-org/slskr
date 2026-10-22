---
category: fixed
audience: users, operators
area: session
action: none
breaking: false
---
Session command queue saturation now returns `503 Service Unavailable` from HTTP routes. Stalled Soulseek server writes and pings are bounded by the configured inactivity timeout, allowing the existing reconnect path to recover the session.
