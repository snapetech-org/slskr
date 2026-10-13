---
category: security
audience: operators
area: ci-security
action: none
breaking: false
---

CI and tagged release workflows verify the cached RustSec audit tool version, reinstall the pinned version when it is missing or stale, and add its bin directory to `PATH` before running the audit. A cache-schema revision lets repaired binaries use a new immutable cache entry.
