---
category: fixed
audience: users
area: transfers
action: none
breaking: false
---

Route incoming download file connections by peer and negotiated transfer token when the initial handshake uses a zero token. Concurrent uploads and downloads no longer take another download's connection, and unknown tokens leave other transfers intact.
