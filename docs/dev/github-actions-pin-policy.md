# GitHub Actions Pin Policy

slskR workflows pin external actions and cross-repository reusable workflow calls
to reviewed 40-character commit SHAs. Version tags and branches are tracked here
only as review context so updates happen through explicit code review instead of
mutable workflow dependency drift.

Run `scripts/check-workflow-release-policy.sh` after changing `.github/workflows`.
The gate fails if any external `uses:` reference is not pinned to a full commit SHA
or if a pinned action or reusable workflow is missing from this ledger.

| Pinned dependency | Reviewed ref | Pinned commit | Notes |
 --- | --- | --- |
| `actions/checkout` | `v6` | `3d3c42e5aac5ba805825da76410c181273ba90b1` | CI, release, live parity, and local identity checkout. |
| `actions/cache` | `v6.1.0` | `55cc8345863c7cc4c66a329aec7e433d2d1c52a9` | Cached pinned `cargo-audit` binaries for CI and release gates. |
| `dtolnay/rust-toolchain` | `stable` | `29eef336d9b2848a0b548edc03f92a220660cdb8` | Rust toolchain install for CI, release, and live parity jobs. |
| `Swatinem/rust-cache` | `v2` | `c8037a86dde8214a8310e9f54a8fc61ab362aa31` | Dereferenced tag target for Rust cache setup. |
| `actions/setup-node` | `v7.1.0` | `949feb2413d6458794dcd2491c4babbbce0c15c1` | Node setup for web, dashboard, TypeScript SDK, and live parity gates; action runtime uses Node 24 and requires runner 2.327.1 or later. |
| `actions/setup-go` | `v7.1.0` | `b7ad1dad31e06c5925ef5d2fc7ad053ef454303e` | Go SDK test setup. |
| `actions/setup-python` | `v7.1.0` | `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0` | Python SDK and slskd API compatibility smoke setup. |
| `actions/setup-dotnet` | `v6.1.0` | `0f4a354dd5547a28c70b7853dbd95d5b67886e73` | Workspace-local .NET 10 SDK for controller regex differential builds. |
| `astral-sh/setup-uv` | `v10.3.0` | `1c37ad07a6a961277cf70c0d37d6f313000f5884` | Installs pinned uv and activates Python 3.12 on the trusted local runner. |
| `actions/upload-artifact` | `v7.0.2` | `cf430e030ddbb5b0abf93d22962f4752f3646cd9` | CI platform, release archive, and live parity artifact upload. |
| `actions/download-artifact` | `v8.0.2` | `9000827ccba6bdab643e8b6fd33ac0654aef8333` | Release archive download before publishing. |
| `actions/attest-build-provenance` | `v4` | `4d101475d8b20a2381f78447822ac1eab6504dd8` | Dereferenced tag target for release asset attestations. |
| `softprops/action-gh-release` | `v3.0.4` | `8a0cd651e5b2365bd640854a3fa5dfc70e4875f3` | GitHub Release publisher. |
| `docker/setup-qemu-action` | `v4.4.0` | `99012661954931238ded8c8b007157a8430204e1` | QEMU setup for multi-architecture Docker release images. |
| `docker/setup-buildx-action` | `v4.4.1` | `f87e5991a6d7451dcb8d9637bfbc97413f497069` | Docker Buildx setup for multi-architecture release images. |
| `docker/login-action` | `v4.8.0` | `8aa5831fb8d48d8f76594c7ddde61ae58019f550` | GHCR and Docker Hub authentication for release images. |
| `docker/build-push-action` | `v7.4.0` | `c3c9e263c25d99ce0380d002d59b67737d91b0dc` | Multi-architecture Docker release image build and push. |
| `aquasecurity/setup-trivy` | `v0.2.6` | `81e514348e19b6112ce2a7e3ecbafe19c1e1f567` | Pins the Trivy install script checkout to a reviewed commit. |
| `snapetech-org/slskr/.github/workflows/web-assets-validation.yml` | `713676d58f1601a8079257f3f4aeefdc0de7b7f6` | `713676d58f1601a8079257f3f4aeefdc0de7b7f6` | Audited reusable workflow for fork-only JIT web asset validation. |

To update an action, resolve the new trusted ref, replace the workflow SHA and the
matching policy row in the same change, and run focused verification.
