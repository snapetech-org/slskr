---
category: security
audience: operators
area: ci-security
action: none
breaking: false
---

CI and tagged release workflows ensure the RustSec audit tool is installed and add its bin directory to `PATH` before running the audit, even when the cache reports a hit.
