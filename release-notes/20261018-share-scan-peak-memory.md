---
category: fixed
audience: users, operators
area: shares
action: none
breaking: false
---
Large share scans now move each root's indexed files and local paths into the combined index rather than cloning the full result. This lowers peak memory during rescans while preserving the existing scan limits and complete-index checks.
