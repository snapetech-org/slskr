---
category: security
audience: operators
area: validation-security
action: none
breaking: false
---
Trusted validation snapshots now reject qualified credential filenames in dot-separated and camel-case forms, exact generic credential basenames with source extensions, and credential directories outside source trees. Auth filenames match only when `auth` is terminal before the extension, preserving source files such as `peer_authentication.rs` and metadata such as `*-controller-auth-policy.json`. Ordinary service names such as `token-parser` and `secrets-manager` remain available in validation snapshots, and only the known dashboard API keys page is exempt from the API-key filename filter.
