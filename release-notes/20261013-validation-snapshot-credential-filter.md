---
category: security
audience: operators
area: validation-security
action: none
breaking: false
---
Validation snapshots now exclude qualified credential filenames and exact credential basenames with source extensions. Auth matching requires `auth` at the end of a filename, so legitimate files such as `peer_authentication.rs` and `*-controller-auth-policy.json` remain available. Common source files and service directories remain accessible.
