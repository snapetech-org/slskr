---
category: fixed
audience: users, operators
area: packaging
action: Refresh the Nix flake from main after release metadata is updated.
breaking: false
---
Nix packages enter the extracted archive root and use static Linux binaries, so installation and execution work without a conventional system ELF loader. Metadata refreshes also preserve the Unraid template's floating latest image reference.
