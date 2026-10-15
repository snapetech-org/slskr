---
category: security
audience: users, operators
area: network-security
action: none
breaking: false
---
Updated the Rust TLS dependency to address four upstream security fixes: bounded Brotli certificate decompression before client authentication, redacted secret data from session debug output, protected ServerHello key-exchange hints, and blocked application data after ECH rejection. No configuration changes are required.
