---
category: security
audience: operators
area: ci-security
action: none
breaking: false
---

Validation snapshots exclude dotted or suffixed dotenv credentials, key/token/client-secret files even with source-like extensions, and all files under credential-named folders outside source trees. They retain ordinary assets under Go and Python SDK roots, including `auth` packages, unless filenames explicitly identify credential material.
