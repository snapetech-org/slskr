---
category: fixed
audience: operators
area: packaging
action: Refresh Snap packages from the new release.
breaking: false
---
Snap packaging uses the Ubuntu 24.04 base required by the native release binaries. A manual publisher verifies release checksums, builds both supported architectures on matching hosted runners, retains the packages, and publishes to the stable channel using configured store credentials.
