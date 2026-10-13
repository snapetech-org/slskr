---
category: fixed
audience: users, operators
area: transfer-capacity
action: Raise explicit scan_max_files and transfers.max_active values that still use the old defaults.
breaking: false
---
Share scans default to 250,000 files and retain the last complete index after a capped or failed scan. Upload/download defaults are 20/500, with 520 shared slots. Starts, resumes, batch requests, alternate-source retries, and retry backoffs now honor capacity limits; upload group limits also apply to manual starts and queued resumes.
