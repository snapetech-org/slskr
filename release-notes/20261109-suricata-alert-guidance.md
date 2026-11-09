---
category: added
audience: operators
area: security
action: Verify the SID and matching traffic before using the documented scoped workaround; alert suppression can leave IPS drops active.
breaking: false
---
The README links to guidance for the reproduced Soulseek collision with ET
Suricata SID 2055754. The guide includes diagnostic steps, mitigation limits,
and a benign offline packet fixture with checks for alert suppression and IPS
behavior. No protocol changes or automatic firewall exceptions are introduced.
