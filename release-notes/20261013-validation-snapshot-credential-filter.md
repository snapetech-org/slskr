---
category: security
audience: operators
area: validation-security
action: none
breaking: false
---
Trusted validation snapshots now reject qualified generic, token, and key credential filenames in dot-separated and camel-case forms, plus credential directories outside source trees. Ordinary service names such as `token-parser` and `secrets-manager` remain available in validation snapshots, and only the known dashboard API keys page is exempt from the API-key filename filter.
