---
category: fixed
audience: operators
area: release
action: Retry Winget publishing from main after a failed submission; keep existing fork history.
breaking: false
---
Winget submissions use canonical GitHub API URLs and a new branch based on Microsoft upstream, containing only the three package manifests. Matching retries reuse the existing PR; mismatched content fails instead of overwriting it. The publisher no longer resets a diverged fork or depends on authenticated write redirects in wingetcreate.
