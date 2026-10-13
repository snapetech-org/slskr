---
category: fixed
audience: users, operators
area: transfer-capacity
action: Raise explicit scan_max_files and transfers.max_active values that still use the old defaults.
breaking: false
---
Share scans now default to 250,000 files and keep the last complete index when a scan hits a cap or filesystem error. Upload and download slot defaults are 20 and 500, with the combined active-transfer cap raised to 520.
