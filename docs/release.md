# slskr Release Runbook

This is the release-prep path for binary archives. `slskr` is a single Rust
binary plus the production React/Vite Web UI assets staged as `web/build`.

## Local Gate

```sh
scripts/run-release-gate.sh
```

This runs public-posture checks, shell syntax checks, Rust formatting, clippy,
workspace tests, RustSec audit when `cargo-audit` is installed, workspace
packaging, web tests, Rust/WASM web checks, the Rust web UI headless parity
audit, and subpath smoke checks.

GitHub CI and tagged release workflows check the cached `cargo-audit` version,
install the pinned version when it is missing or stale, and add its bin directory
to `PATH` before running the RustSec audit. The versioned cache key includes a
schema revision so a repaired executable can be saved separately from older
immutable entries. Local runs may skip the audit when the tool is not installed.

All compile-capable Cargo commands in this repository use the normal Rust
toolchain. The workspace config keeps the large daemon crate on one Cargo job,
turns off unnecessary dev debug metadata, and uses 16 codegen units with
ThinLTO for release builds:

```sh
cargo build --release -p slskr
cargo test --workspace
```

Rust formatting uses `scripts/check-rust-format.sh`, which checks changed source
files individually and compares emitted output locally rather than asking
rustfmt to construct the monolithic controller's full diff.

The `slskr` package defaults to its focused controller-test target. The
historical monolithic controller suite remains an explicit opt-in with
`--features full-controller-tests`; the default workspace test path keeps that
large proof module out of ordinary edit/test cycles.

Browser and frontend Node subprocesses in the parity and release gates use
`scripts/with-process-memory-guard.sh`; Rust commands do not. This keeps the
non-Rust browser tooling bounded without imposing its smaller process cap on
LLVM.

The live slskd automation-client compatibility smoke is opt-in because it starts
a local daemon and may install the Python `slskd-api` package:

```sh
SLSKR_RUN_SLSKD_API_COMPAT_SMOKE=1 scripts/run-release-gate.sh
```

CI also runs a lighter scheduled/manual `Live Parity` workflow. That workflow
executes the Rust web UI headless parity audit and the hermetic local
`slskd_api` automation compatibility smoke, then uploads the Rust UI screenshots,
web bundle, and daemon log as artifacts. The same workflow also has an optional
credentialed public-live job: when the `SLSKR_LIVE_INTEROP_ENV` repository secret
contains the same env-file variables used by `scripts/run-live-interop-matrix.sh`,
CI runs login, local peer, private-message, and room-message probes and uploads
`target/live-interop`; when the secret is absent, it uploads an explicit skipped
TSV artifact.

The daily/manual `React Nightly Audit` runs the React UI against deterministic
mock responses and retains browser reports, screenshots, and source-bound
receipts for 30 days. It verifies desktop/mobile rendering and four workflow
scenarios; deployed-device and credentialed interop evidence are separate.

To validate a released Chocolatey package on a clean Windows runner without
publishing it, dispatch the existing workflow with `publish=false`:

```sh
tag="$(git describe --tags --match 'v*' --match 'release-v*' --abbrev=0)"
gh workflow run publish-chocolatey.yml --ref main -f tag="$tag" -f publish=false
```

The command selects the newest release tag reachable from the current checkout;
set `tag` directly to inspect another release. The workflow verifies the
downloaded release asset against `SHA256SUMS.txt`, packs and checks the nupkg,
and retains the package and a source-bound receipt for 30 days. The default
`publish=true` preserves the manual publication flow and requires configured
credentials.

## Local Archive

Build the host archive:

```sh
scripts/build-release-archive.sh --version dev-local
scripts/verify-release-artifacts.sh target/dist
```

The archive includes:

- `slskr` or `slskr.exe`
- `web/build` with `index.html`, hashed JavaScript/CSS assets, icons, and the
  web app manifest
- `README.md`, `LICENSE`, `NOTICE`, `COMPLIANCE.md`
- `docs/slskr.config.example.toml`
- `RUN.txt`

Release archive builds normalize `SLSKR_RELEASE_VERSION` and embed it as the
application version while internal Cargo crates remain at `0.0.0`. The archive
verifier checks `slskr version` on a matching host platform and verifies the
archive contents without attempting to execute a foreign-platform binary.

## Release notes and changelog

User-facing, security, operational, and user-facing documentation changes add
one new validated fragment under `release-notes/`. The validation workflow
requires that fragment or an explicit internal-only selection, and fragments
are append-only. Each fragment records its category, audience, product area,
required action, and breaking-change status.

Preview the grouped release text locally with:

```sh
python3 scripts/release_notes.py preview --base <base> --head <head>
```

The tag workflow publishes a concise curated body as `release/RELEASE_NOTES.md`
and sends that same summary in the Discord embed. It also uploads the complete
machine-validated fragment assembly as `release/RELEASE_NOTES_FULL.md`, keeping
the release page readable without discarding detailed change history. The
validation job exposes a separate capture-metadata table so the source
fragment fields remain auditable. Keep `CHANGELOG.md` append-only at the
release-section level and move shipped `## [Unreleased]` bullets into a dated
section when preparing a release; the CI and tag workflows reject a missing or
placeholder section.

## CI and release matrix

The `CI` workflow is started with a manual dispatch using `action_tag=test` and
`runner_pool_tag=private`. For a release, dispatch it on the release tag and
wait for the exact-tag, exact-commit run to pass. Each matrix job builds a target
archive, verifies its checksum and layout, and uploads the archive for seven
days so a platform-specific build can be downloaded for testing. Native
workspace tests run on Linux x64, Linux AArch64, both macOS architectures, and
Windows; the additional musl jobs smoke test their built static binary through
the same archive verifier.

The release workflow uses the same native runner and target mapping:

| Target | CI and release runner | Rust target | CI exercise |
| --- | --- | --- | --- |
| `linux-x64` | Private JIT Linux x64 | `x86_64-unknown-linux-gnu` | Full Linux tests and archive smoke |
| `linux-musl-x64` | Private JIT Linux x64 | `x86_64-unknown-linux-musl` | Static archive build and smoke |
| `linux-arm64` | Private JIT Linux ARM64 | `aarch64-unknown-linux-gnu` | Full AArch64 tests and archive smoke |
| `linux-musl-arm64` | Private JIT Linux ARM64 | `aarch64-unknown-linux-musl` | Static archive build and smoke |
| `macos-x64` | Private JIT macOS x64 | `x86_64-apple-darwin` | Native workspace tests and archive smoke |
| `macos-arm64` | Private JIT macOS ARM64 | `aarch64-apple-darwin` | Native workspace tests and archive smoke |
| `windows-x64` | Private JIT Windows x64 | `x86_64-pc-windows-msvc` | Native workspace tests and archive smoke |

Create and push a version tag named:

```text
v<semver>
```

Use `v<semver>`, for example `v1.2.3` or `v1.2.3-rc.1`. Existing
`release-v<semver>` tags remain supported for compatibility. Commits pushed to
`main` do not start CI or release workflows. After the tag exists, manually
dispatch CI on that tag with `action_tag=test` and
`runner_pool_tag=private`. Once that exact run succeeds, manually dispatch
Release on the same tag with `action_tag=release`, `runner_pool_tag=private`,
and the identical `tag` input. The release workflow checks the selected ref,
requested tag, and successful private CI result before publishing. Use a tag
pointing to the reviewed `main` commit.

For a release build, the workflow creates a GitHub Release and uploads all archives
plus `SHA256SUMS.txt`, `slskr-cyclonedx.json`, and
`slskr-dependency-manifest.json`. The JSON manifests are included in the
release checksum file and build-provenance attestation subjects.
After the GitHub Release is published, the workflow posts a Discord
announcement using the `DISCORD_RELEASE_WEBHOOK_URL` repository secret.

The internal/unpublished Cargo crates intentionally remain at `0.0.0`. Binary
and archive version metadata comes from the release workflow. Tag builds derive
the artifact version from `v<semver>` (or a legacy `release-v<semver>` tag), and local/manual archive tests
can still pass `SLSKR_RELEASE_VERSION` directly to
`scripts/build-release-archive.sh`.
Archive roots are named `slskr-<version>-<target>` so the published package
version remains tied to the release input even though the workspace crates are
not published independently.
