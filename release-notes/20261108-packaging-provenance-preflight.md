---
category: fixed
audience: operators
area: release
action: none
breaking: false
---
Packaging policy validates the immutable release-tag commit used by publisher recovery. A fast preflight runs packaging rules and their regression tests before native compilation, so stale policy assertions fail before the platform builds start.
