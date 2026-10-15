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

## [0.2.64] — 2026-10-15

- [Internal-only] Replace incomplete default CodeQL coverage with a pinned
  advanced workflow that scans Actions, C/C++, Go, JavaScript/TypeScript,
  Python, Ruby, and Rust.
- [Internal-only] Refresh the release-gate inventory snapshots to the current
  source digest and candidate counts.

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
