---
category: fixed
audience: operators
area: release
action: Check the final required release stage and publisher receipts before treating a release as complete.
breaking: false
---
A required final gate rejects failed, cancelled, missing, or skipped build, publisher, and announcement stages. Publisher credential preflight prevents optional no-op publishing. Tagged downstream workflows receive explicit caller context. Snap publishing remains excluded by the owner directive for this release.
