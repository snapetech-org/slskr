---
category: fixed
audience: users, operators
area: shares
action: Upgrade and rescan shares with a scan_max_files limit appropriate for the library.
breaking: false
---
Share-root metadata updates and library, federation, and bridge searches reuse immutable file-list and path-map allocations instead of copying the entire library. Bounded results retain only the selected records before asynchronous metadata or network operations, reducing memory spikes and runtime stalls for large libraries.
