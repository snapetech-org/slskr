---
category: security
audience: operators
area: validation-security
action: none
breaking: false
---
Validation snapshots exclude credential filenames and directories when environment qualifiers precede or follow the credential term, plus exact credential basenames with source extensions. Auth matching requires `auth` to end the filename, preserving `peer_authentication.rs` and `*-controller-auth-policy.json`. Descriptive Markdown remains available under `docs/` and `release-notes/`; credential configuration files remain excluded there. Ordinary camel-case source modules and service directories remain accessible.
