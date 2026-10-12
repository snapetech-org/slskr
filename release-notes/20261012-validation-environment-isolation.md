---
category: security
audience: operators
area: validation
action: none
breaking: false
---

Validation task identifiers are checked before use in per-task filesystem paths. Task and runtime-probe processes also use restricted environment variables and private temporary settings, reducing exposure of unrelated credentials and configuration during validation.
