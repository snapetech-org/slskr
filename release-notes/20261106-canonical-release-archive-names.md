---
category: fixed
audience: users, operators
area: packaging
action: Update packages from the new release.
breaking: false
---
Release archives retain the canonical version prefix expected by package managers and installers. Release validation now builds a real fixture archive using the workflow's version input and checks its filename, layout, embedded application-version input, and checksum against the package consumer contract.
