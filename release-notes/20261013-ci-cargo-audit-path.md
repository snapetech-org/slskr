---
category: security
audience: operators
area: ci-security
action: none
breaking: false
---

CI and tagged release workflows verify that the cached RustSec audit tool exists and add its bin directory to `PATH` before running the audit.
