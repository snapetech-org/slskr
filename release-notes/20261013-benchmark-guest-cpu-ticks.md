---
category: changed
audience: operators
area: performance
action: none
breaking: false
---
The idle benchmark now excludes guest CPU ticks that Linux already includes in user and nice time. Retained October 12 host-busy figures are labeled as legacy estimates because their raw per-field tick deltas were not saved.
