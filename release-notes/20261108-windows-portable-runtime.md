---
category: fixed
audience: users
area: windows
action: Use the new portable Windows archive without installing a separate Visual C++ runtime.
breaking: false
---
Windows binaries link the C runtime statically. Archive verification rejects VCRUNTIME, MSVCP, MSVCR, and CONCRT imports that would require an external redistributable. Native Windows smoke validation builds the executable, checks its PE imports, and runs its version command.
