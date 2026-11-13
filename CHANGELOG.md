# Changelog

All notable changes to slskr are documented here. Release pages are generated
from the tagged source by the release workflow, with structured fragments from
`release-notes/` assembled into the user-facing release section.

Use release sections in this form:

```markdown
## [<version>] — YYYY-MM-DD
```

Keep the file append-only at the release-section level. Add shipped user-facing
bullets to `## [Unreleased]`, then move them into the dated version section when
the release is prepared. Do not rewrite audited release history.

---

## [Unreleased]

## [0.2.104] — 2026-11-13

- Route ARM64 Ubuntu archive, update, and security suites through the Ports mirror so hosted package validation can proceed.

## [0.2.103] — 2026-11-13

- Update the QUIC protocol and UDP dependencies to patched releases, fixing three newly reported RustSec denial-of-service advisories.

## [0.2.102] — 2026-11-13

- Resume downloads after Soulseek peers confirm `QueueUpload` or reconnect, matching the peer and transfer token so remote queues do not leave downloads stuck.
- Preserve opted-in browser sessions across daemon restarts and refresh them only with the credentials that issued them.
- Refresh vulnerable build and runtime dependencies, including the Web toolchain and container packages.
- Route hosted Ubuntu archive, security, and ARM sources through separate failover lists without nesting runner mirror lists; stop when indexes cannot be refreshed.

## [0.2.101] — 2026-11-13

- Resume downloads after Soulseek peers confirm `QueueUpload` or reconnect, matching the peer and transfer token so remote queues do not leave downloads stuck.
- Preserve opted-in browser sessions across daemon restarts and refresh them only with the credentials that issued them.
- Refresh vulnerable build and runtime dependencies, including the Web toolchain and container packages.
- Route hosted Ubuntu archive, security, and ARM sources through separate failover lists without nesting runner mirror lists; stop when indexes cannot be refreshed.

## [0.2.100] — 2026-11-13

- Resume Soulseek downloads when peers confirm a remote queue or reconnect, using the `QueueUpload` protocol and validating the peer and transfer token.
- Preserve browser sessions across daemon restarts, with refresh tokens bound to the credentials that issued them.
- Refresh build and runtime dependencies, including TypeScript 7.0.2, browser-test tooling, and container packages.
- Fail over Ubuntu package downloads across ordered, independently hosted mirror lists, and reject stale package indexes when all mirrors fail.

## [0.2.99] — 2026-11-13

- Preserve web sessions across daemon restarts, restricting token refresh to the credentials that issued the token.
- Negotiate downloads through Soulseek's `QueueUpload` protocol and re-request remote-queued downloads after reconnect.
- Refresh vulnerable build and runtime dependencies, including the Web toolchain and container packages.

## [0.2.98] — 2026-11-12

- Preserve controller web sessions across daemon restarts, with session refresh restricted to the credentials that issued the token.
- Negotiate downloads with peers using `QueueUpload`, and re-request remote-queued downloads after reconnect.
- Refresh vulnerable build and runtime dependencies, including the Web toolchain and container packages.

## [0.2.97] — 2026-11-12

- Keep browser sessions alive across daemon restarts, with opt-in Remember Me and refresh bound to the current web-auth credentials.
- Patch Python development tools, remove vulnerable native compiler payloads from the Web build, and refresh container operating-system packages.

## [0.2.96] — 2026-11-12

- Resume peer-queued downloads after a confirmed queue response and reconnect, while validating the callback peer and transfer token and enforcing local download-slot limits.

## [0.2.95] — 2026-11-12

- Resume peer-queued downloads when the uploader reconnects with the matching transfer token, while enforcing local download-slot limits.

## [0.2.94] — 2026-11-11

- Resume queued downloads when the uploader starts the transfer on a new regular or obfuscated peer connection, including after the original connection closes or times out.
- Match incoming file connections to their peer and negotiated transfer token so concurrent uploads and downloads cannot claim another download's connection.
- Preserve remote upload queue scheduling and use independent mirrors of signed Ubuntu packages during Ubuntu DNS outages.

## [0.2.93] — 2026-11-11

- Resume queued downloads when the uploader starts the transfer on a new regular or obfuscated peer connection.
- Keep remote queues pending when the original connection closes or times out, and preserve downloads already accepted on another connection.
- Use independent mirrors of signed Ubuntu packages so Ubuntu DNS outages do not block release jobs.

## [0.2.92] — 2026-11-11

- Resume queued downloads when the uploader starts the transfer on a new regular or obfuscated peer connection.
- Keep remote queues pending when the original connection closes or times out, and preserve downloads already accepted on another connection.
- Use Ubuntu's standard package mirror for hosted build and release jobs when the Azure mirror cannot resolve.

## [0.2.91] — 2026-11-11

- Resume queued downloads when the uploader starts the transfer on a new regular or obfuscated peer connection.
- Keep remote queues pending when the original connection closes or times out, and preserve downloads already accepted on another connection.

## [0.2.90] — 2026-11-10

- Finish music library scans when individual files are unreadable, and log each retained warning with its path and operating-system error.
- Keep share browse and local search available after skipped files by reporting warnings separately from fatal scan errors (#213).
- Preserve the previous share index when a directory is inaccessible or a scan safety limit is reached.
- Update bundled SQLite to 3.54.1 to fix CVE-2026-119375.

## [0.2.89] — 2026-11-10

- Finish music library scans when individual files are unreadable, and log each retained warning with its path and operating-system error.
- Keep share browse and local search available after skipped files by reporting warnings separately from fatal scan errors (#213).
- Preserve the previous share index when a directory is inaccessible or a scan safety limit is reached.
- Update bundled SQLite to 3.54.1 to fix CVE-2026-119375.

## [0.2.88] — 2026-11-10

- Skip unreadable music files, log their paths and operating-system errors at Warning level, and finish indexing readable files.
- Preserve the previous share index if a share directory is inaccessible or a scan safety limit is reached.
- Update bundled SQLite to 3.54.1 to fix CVE-2026-119375.

## [0.2.86] — 2026-11-07

- Ship portable Windows archives with the Visual C++ runtime linked statically.
- Verify configured publishers and public package availability before announcing release completion.
- Keep Chocolatey pending initial approval without further submissions, and exclude Snap Store publication by owner instruction.
- Validate packaging provenance and policy in an independent preflight with explicit hosted-runner tool setup.

## [0.2.85] — 2026-11-07

- Ship portable Windows archives with the Visual C++ runtime linked statically.
- Verify every configured publisher and public package availability before announcing release completion.
- Preserve explicit pending status for Chocolatey's initial review without further submissions; Snap Store publication remains excluded by owner instruction.
- Bind publisher recovery provenance to the immutable release tag and validate packaging policy before native compilation.

## [0.2.84] — 2026-11-07

- Link the Visual C++ runtime statically so portable Windows packages start without an undeclared redistributable dependency.
- Require Chocolatey publication alongside every other configured publisher before announcing release completion.
- Recover Winget submissions without rewriting fork history, and verify existing submissions before retrying them.
- Verify public package availability before announcing completion, including asynchronous repository builds and catalog review.
- Retain prepared Chocolatey packages without further uploads while the first submission awaits approval, when explicitly authorized.

## [0.2.83] — 2026-11-07

- Require every native build, downstream publisher, and Discord announcement to succeed before the release workflow can pass.
- Fail early when package publisher credentials are missing and restore automatic tagged downstream publishing.
- Confirm Discord delivery and support announcement recovery using the current published release notes.
- Include the large-library indexing, stalled-search recovery, security dependency, and static Linux compatibility fixes shipped in 0.2.82.

## [0.2.82] — 2026-11-06

- Keep large share indexes shared during scan publication, configuration reloads, and bounded library/federation reads; failed rescans retain the last complete index.
- Recover stalled searches through bounded session queues and server writes.
- Refresh vulnerable dependencies and restore native public GitHub-hosted builds and release publishing.
- Publish canonical package archive names and static Linux packages compatible with older system libraries.

## [0.2.81] — 2026-11-06

- Fix large-library share-index publication stalls and preserve complete indexes after failed rescans.
- Recover stalled searches through bounded session queues and server writes.
- Refresh vulnerable dependencies and restore native public GitHub-hosted release validation.
- Publish canonical archive names consumed by package managers, with static Linux packages for older system libraries.

## [0.2.80] — 2026-11-06

- Publish large-library share indexes without duplicating the full index and preserve the last complete index after failed rescans.
- Recover stalled searches with bounded session-command admission and server writes.
- Ship static Linux packages compatible with older system libraries and refreshed security dependencies.
- Restore public GitHub-hosted builds and downstream release publishing, with full release shell lint enforced in CI.

## [0.2.79] — 2026-11-06

- Publish completed large-library share indexes without a full duplicate allocation; failed rescans retain the last complete index.
- Bound session-command queue admission and server writes to recover stalled searches.
- Keep Debian/PPA, RPM, Linux Homebrew, and Linux installers compatible with older system libraries through static archives.
- Restore native public GitHub-hosted validation and downstream release publishing.
- Remove vulnerable Node tooling dependencies and refresh Rust, frontend, and workflow dependencies.

### User-facing changes

#### Changed

- Refine MediaCore graph-traversal, backfill, and synchronization status wording across all 12 direct locales.
- Localize reviewed media-server and setup-health actions in status views, copied reports, and diagnostic bundles across the direct locales.
- Refine reviewed cryptographic, DHT, and visualizer wording across the 12 direct locales.

### Security

- Replace the unmaintained YAML parser dependency with the pinned safe Rust parser and update `ctutils` to 0.4.4.

## [0.2.76] — 2026-10-21

### User-facing changes

#### Added

- Operators can now sign in to slskR through an OpenID Connect provider, with verified-email admission and the existing controller session kept in place.

#### Changed

- OIDC guidance now explains exact callback setup, verified-email admission, administrator access, recovery, and provider troubleshooting for slskR operators.

#### Fixed

- Concurrent OIDC sign-ins now keep separate short-lived state in the browser tab. Login status and error messages are announced accessibly by assistive technology.
- Stable slskR releases now publish matching `:main` and `:latest` aliases to GHCR and Docker Hub. Unreleased main-branch commits do not move either alias.
- Session command queue saturation now returns `503 Service Unavailable` from HTTP routes. Stalled Soulseek server writes and pings are bounded by the configured inactivity timeout, allowing the existing reconnect path to recover the session.

#### Security

- Patched web dependencies and refreshed TLS trust roots address current advisories while keeping secure HTTPS connections current for slskR users. Node.js CI and container builds are pinned to the patched 22.23.4 runtime.

## [0.2.74] — 2026-10-18

- Reduce peak memory during large share scans by moving per-root results into
  the combined index instead of cloning them.

## [0.2.73] — 2026-10-18

- Reduce peak memory during large share scans by moving per-root results into
  the combined index instead of cloning them.

## [0.2.72] — 2026-10-18

- Reduce peak memory during large share scans by moving per-root results into
  the combined index instead of cloning them.

## [0.2.71] — 2026-10-17


## [0.2.70] — 2026-10-16

- [Internal-only] Pin frozen controller regex probes to invariant .NET
  globalization so runner locale and ICU updates cannot alter parity results.

## [0.2.69] — 2026-10-16

- [Internal-only] Fix shared-runner Git fixture permissions, self-hosted Node
  cache setup, and canonical Winget fork synchronization.

## [0.2.68] — 2026-10-16

- [Internal-only] Route GHCR release pushes through a dedicated credential for
  the personal account that owns the package.

## [0.2.67] — 2026-10-16

- [Internal-only] Make private-runner temporary-file cleanup pass the release
  gate's ShellCheck lint.

## [0.2.66] — 2026-10-16


## [0.2.65] — 2026-10-15


## [0.2.64] — 2026-10-15

- [Internal-only] Replace incomplete default CodeQL coverage with a pinned
  advanced workflow that scans Actions, C/C++, Go, JavaScript/TypeScript,
  Python, Ruby, and Rust.

## [0.2.63] — 2026-10-15

- [Internal-only] Start platform archive builds after exact-commit Main CI while
  the full release gate runs; GitHub Release publication still requires the
  gate and every archive.
- [Internal-only] Split the full transfer controller contracts into bounded
  modules so every Rust source stays under the enforced 2,500-line limit.

## [0.2.62] — 2026-10-15

- [Internal-only] Make blacklist peer probes answer server-initiated UserInfo
  requests and wait for the matching response, avoiding timing-sensitive frame
  ordering in frozen-client comparisons.

## [0.2.61] — 2026-10-15

- [Internal-only] Use fresh HTTP and HTTPS ports for the slskR side of the
  options differential after stopping the upstream daemon, avoiding hosted
  listener rebinding conflicts without changing runtime behavior.

## [0.2.60] — 2026-10-15

- [Internal-only] Rechecked the peer listener immediately before watched
  blacklist probes, waited on UserInfo state instead of replaying full probes,
  and retained stale Browse-cache results for strict target comparison.

## [0.2.59] — 2026-10-15

- [Internal-only] Aligned the runtime-boundary release check with the existing
  bounded share-scan path and descriptor handling proof; runtime behavior is
  unchanged.

## [0.2.58] — 2026-10-14

- Corrected options and integrations parity normalization for the frozen
  slskdN reference's legacy default identity strings; configured-value
  comparisons remain strict and product behavior is unchanged.

## [0.2.57] — 2026-10-14

- Added browser-local interface-language and regional-format preferences across
  navigation, transfer states, dates, metrics, and accessibility labels.
- Expanded Web UI localization across chat, player, SongID, search, network,
  integrations, shares, transfers, and system screens in all twelve locales.
- Updated the Rust TLS dependency to address four upstream security fixes.
- Migrated repository, release, issue, and support links to `snapetech-org/slskr`.
- Fixed release-gate baseline setup for clean checkouts and task-scoped
  temporary paths, including comparison of slskR's share-scan progress field.
- Narrowed secret-scan exceptions to fixed synthetic token sentinels and canary
  values in validation contract fixtures.
- Filter candidate snapshots for credential filenames with multiple leading
  qualifiers or trailing camel-case environment names while preserving ordinary
  source modules and documentation.
- Recorded repeatable idle CPU and memory comparisons for local containers and
  connected Soulseek sessions, with raw measurements and clear scope limits.
- Preserve timestamped failed benchmark attempts and failure reasons in raw
  artifacts so retry counts and denominators can be audited.
- Pull selected benchmark images by pinned digest before recording metadata and
  mark process RSS totals incomplete when procfs samples are missing.
- Hardened local validation with a trusted test sandbox and isolated task
  environments.
- Moved validation-run locks out of shared temporary storage to prevent
  cross-user lock pre-creation.
- Added startup share-scan logs for the start, periodic filesystem-entry
  progress, and final indexed-file count.
- Returned slskd-compatible versioned search and download responses, and delivered
  search results to firewalled peers through server-brokered connections.
- Added a COPR API-token fallback when Fedora Kerberos authentication is
  unavailable.

## [0.2.47] — 2026-10-04

- Improved search loading and recovery, user profile details, mobile navigation,
  and keyboard and screen-reader access across the Web UI.
- Removed donation links from the README and both Web UI shells.
- Hardened share streaming, listener validation, asynchronous shutdown, Python
  WebSocket cancellation, and certification setup and failure reporting.
- Strengthened browser security and audit checks to reject unsafe code paths
  and surface incomplete scans.
- Corrected release-note validation and assembly so accurate product wording
  passes while unsuccessful unpublished tags do not hide pending notes.

## [0.2.42] — 2026-09-30

- Reduced startup share-scan I/O by skipping unsupported media files and using
  bounded, format-specific metadata probes for WAV, FLAC, and MP3 files.
- Removed personal email attribution and machine-specific checkout paths from
  project documentation and recovery records.
- Kept recent-commit leak scanning focused on authored text while ignoring
  standard Git attribution trailers.

## [0.2.41] — 2026-09-29

- Added Rust-specific getting-started, feature, status, configuration,
  architecture, and troubleshooting guides, and corrected the native/current
  shared peer-port documentation.

## [0.2.39] — 2026-09-04

- Expanded required CI to build and verify every supported Linux, macOS, and
  Windows archive on current changes, with native workspace tests where
  available and downloadable test artifacts.
- Repaired Winget fork synchronization with recoverable backups, and aligned
  package metadata, architecture-aware installers, Nix sources, and release
  documentation with the actual artifact matrix.
- Expanded downstream packaging and deployment validation across Linux
  amd64/AArch64, native macOS, Snap, Flatpak, RPM, Debian, containers, and
  supported operator manifests.

## [0.2.38] — 2026-08-30

- Published native Linux x86-64 and AArch64 GNU/musl, macOS Intel and Apple
  silicon, and Windows archives with checksums, dependency manifests, and
  build provenance.
- Hardened compatibility-profile routing, Soulseek transport, transfer and
  persistence lifecycles, and the React Web UI's error and reconnect paths.
- Refreshed downstream package metadata and release validation for the current
  archive matrix.

## [0.2.34] — 2026-08-28

- Aligned native/current networking with current upstream shared-port behavior,
  including bounded Soulseek/TLS mesh TCP demultiplexing and VPN-forwarded
  port updates.
- Improved Web UI identity and interactions, including login, Dropdown and
  Modal behavior, sharing access, stream permissions, and grant contracts.
- Hardened Rust and process memory guards, formatting/build tooling, and
  release and browser validation workflows.
- Fixed release validation to resolve frozen slskd authentication checks
  against the renamed legacy policy registry.
- Fixed options differential validation to ignore only known default product
  identity fields while preserving strict checks for configured values.
- Preserved the historical dedicated obfuscated listener for frozen native
  compatibility profiles while keeping current native deployments on the
  merged public listener.
- Preserved frozen-profile Lidarr import request compatibility while retaining
  the current upstream already-owned album pre-check in current native mode.

## [0.2.33] — 2026-08-23

- Fixed share scanning for large libraries with thousands of top-level
  directories while retaining bounded resource use and symlink safety.
- Matched frozen-profile configuration-watch behavior for malformed YAML by
  clearing the transient options projection while retaining the live share
  index until a valid reload.
- Improved VPN-scoped live validation for listener metadata, browse, API
  authentication, queued transfers, hash verification, and session soak.
- Expanded public Soulseek acceptance across the available credential pool,
  including plain, obfuscated, distributed, indirect, messaging, and transfer
  paths.

## [0.2.32] — 2026-08-21

- Added bounded release, parity, interop, and browser-audit workflows with
  structured release-note assembly and multi-platform archive publication.
- Fixed compatibility-profile routing, protocol/session stability, persistence
  contention handling, and the React Web UI's error, CSP, modal, and automation
  surfaces.
- Added live MusicBrainz, discovery, MediaCore, Soulseek, transfer, messaging,
  and system-surface coverage to the acceptance evidence.
- Published release pages now use a concise proof-linked summary while retaining
  the complete structured fragment assembly as a downloadable release asset.
