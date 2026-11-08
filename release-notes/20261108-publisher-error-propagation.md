---
category: fixed
audience: operators
area: release
action: none
breaking: false
---
Package publishers fail when credentials are missing. Homebrew retries distinguish an unchanged formula from a failed Git comparison, commit, or push, so publication errors cannot appear as successful releases.
