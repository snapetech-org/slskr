---
category: fixed
audience: users
area: shares
action: none
breaking: false
---
Music library scans now skip individual unreadable files instead of failing the entire scan. Warnings identify each skipped file and its operating-system error without requiring Trace logging, with bounded diagnostics for large numbers of unreadable files. Unavailable directories and scan safety limits still fail safely without replacing the previous share index.
