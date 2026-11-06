---
category: fixed
audience: users, operators
area: packaging
action: Update packages and containers from the new release.
breaking: false
---
Debian/PPA, RPM, Linux Homebrew, and Linux installers consume static archives so older system libraries can run binaries built on hosted runners. CI checks startup on Ubuntu 22.04 and Debian 12. Docker and AUR use the actual release tag. Installers handle tag formats, checksum prefixes, and archive roots.
