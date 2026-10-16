---
category: fixed
audience: operators
area: release-pipeline
action: none
breaking: false
---
Release-gate controller regex comparisons now run frozen .NET references with invariant globalization, preventing host locale and ICU updates from changing the result. The slskR regex behavior itself is unchanged.
