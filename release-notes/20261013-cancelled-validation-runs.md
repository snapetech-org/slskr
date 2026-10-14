---
category: changed
audience: operators
area: validation
action: none
breaking: false
---
Canceled superseded pull-request runs now skip final receipt reconciliation so the newest run can start without waiting behind an obsolete queue slot. Failures in the current run still receive full reconciliation.
