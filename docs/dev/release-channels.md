# Release Channels

slskR publishes downstream packages from `.github/workflows/release-publish.yml`
as a required reusable job after the tag release uploads its assets. GHCR
publication and the published-image shutdown smoke test must pass before the
release workflow completes. The workflow reuses the same account layout as the
slskdN release system, with slskR-specific package and project names.

| Channel | Target | Credentials |
| --- | --- | --- |
| GitHub Container Registry | `ghcr.io/snapetech/slskr` | `GHCR_TOKEN` (classic PAT with `write:packages`) |
| Docker Hub | `snapetech/slskr` | `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` |
| AUR source package | `slskr` | `AUR_SSH_KEY` |
| AUR binary package | `slskr-bin` | `AUR_SSH_KEY` |
| COPR | `slskdn/slskr` (x86_64 and aarch64) | Preferred: `COPR_KERBEROS_PRINCIPAL`, `COPR_KERBEROS_KEYTAB_B64`; then Fedora username/password/TOTP; last fallback: `COPR_LOGIN`, `COPR_TOKEN` |
| Launchpad PPA | `~keefshape/ubuntu/slskdn` (amd64; arm64 source-ready) | `GPG_PRIVATE_KEY`, optional `LAUNCHPAD_SFTP_KEY`, optional `LAUNCHPAD_SFTP_USER` |
| Homebrew tap | `snapetech-org/homebrew-slskdn` (`snapetech/homebrew-slskdn` compatibility redirect) | `TAP_GITHUB_TOKEN` |
| Snap | `slskr` (amd64 and arm64) | `SNAPCRAFT_STORE_CREDENTIALS` in the manual `publish-snap.yml` workflow |
| Flatpak manifest | `io.github.slskd.slskr` (x86_64 and aarch64) | no Flathub publisher configured in this repository |
| Helm | `packaging/helm/slskr` (multi-arch GHCR image) | none |
| TrueNAS SCALE | `packaging/truenas-scale/charts/slskr` (multi-arch GHCR image) | none |
| Unraid | `slskr.xml` (repository root; floating `latest` GHCR tag) | none |
| Synology SPK | `packaging/synology-spk` (x86_64 or aarch64 build) | none |
| Winget | `snapetech.slskr` (Windows x64) | `WINGETCREATE_GITHUB_TOKEN` |
| Chocolatey | `slskr` (Windows x64) | `CHOCO_API_KEY` |
| Nix flake | `slskr` | none |

All configured package publishers are required for a full release. Missing
credentials fail preflight; they must not turn publication into a successful
no-op. A targeted recovery retries only the selected failed publisher after the
other destinations have actual publication receipts. It is not a substitute for
verifying every required channel. Snap remains excluded by the owner's current
release directive; do not extend that exception to another publisher.
GHCR uses a classic personal access token
because the `slskR` package belongs to the personal `snapetech` account rather
than the `snapetech-org` repository. Both registries receive the same verified
release before the container publishing job completes. The
Winget job submits a pull request to Microsoft's repository; a successful job
does not mean that Microsoft has merged or indexed the package. Chocolatey is a
required reusable job in the tagged release workflow and derives its package
version and Windows archive checksum from that tag. Its manual workflow remains
available for validation and recovery. Chocolatey publication failures block
Discord and the final completion gate.

## Publication boundaries

The release workflow directly publishes GitHub release assets, both GHCR and
Docker Hub multi-architecture images, AUR, COPR, the Launchpad PPA, the Homebrew
tap, and Chocolatey packages. It submits Winget manifests for external review. The release CI also validates the Snap and Flatpak manifests and their
architecture-specific source archives, while the separate manual `publish-snap.yml` workflow builds and uploads both
Snap architectures after the release assets exist. The checked-in Flatpak
manifest and its download validation do not constitute a Flathub submission.
Flathub requires a separately verified app repository, publisher, and review
process; do not report an upload without an actual receipt.

The 2026-09-06 audit found the Launchpad source publication fully accepted and
its `amd64` build successful, but the public PPA scheduled no `arm64` build.
The Debian control file and repository CI support both architectures; enabling
the PPA's `arm64` builder is an account-level Launchpad operation and must be
completed before describing the PPA itself as multi-architecture.

Helm, TrueNAS, Unraid, Synology, and Nix are checked-in consumers or build
metadata. They point at the published archives or GHCR image, but this
repository does not claim that a separate catalog has received a publication
unless the corresponding workflow explicitly performs that upload. The Unraid
Community Apps template at the repository root (`slskr.xml`) is submitted to
the external Community Apps catalog at `ca.unraid.net/submit`; catalog review
and listing are external and are not performed by a slskR workflow. The
template tracks the floating `latest` GHCR tag so catalog installs always pull
the newest published release; the release metadata refresh does not commit
changes back to the repository.

## Confirming completion

A successful submission is not the same as repository availability. Confirm the
native archives, checksums and provenance; both registry aliases and native
platform manifests; AUR versions and the actual tap formula; all COPR builds and
public RPM indexes; and the Launchpad build plus public apt index. Record Winget
and Chocolatey validation/moderation states separately from submission receipts.
Do not describe an external catalog as indexed while it is still reviewing a PR
or package. Use the recovery commands in `docs/release.md` and retain their
actual package hashes and provider responses.

## COPR Authentication

COPR publishing prefers a keytab-backed Kerberos/GSSAPI principal because Copr
API tokens expire. If no keytab is configured, the workflow tries Fedora
username/password/TOTP credentials before falling back to the Copr API token.
Store a keytab-backed principal in OpenBao, then let `github:sync-secrets`
propagate it to GitHub Actions:

```bash
scripts/store-copr-kerberos-openbao.sh \
  --principal '<principal>@FEDORAPROJECT.ORG' \
  --keytab /path/to/copr.keytab
```

Keep `COPR_LOGIN` and `COPR_TOKEN` configured only as a last fallback while the
preferred Kerberos or Fedora password+TOTP path is being validated. The
workflow uses the token only when the other credential sets are incomplete.

Debian/PPA, RPM, Linux Homebrew, Nix on Linux, and Linux installers use static musl archives
so their binaries work with older system libraries. Both GNU archive targets
remain available independently. CI starts the static x64 binary on Ubuntu 22.04
and Debian 12 before accepting package builds.

The Nix flake follows the generated release metadata on `main`. To pin a
published package, pin its metadata-refresh commit; application version tags
are created before the release archive hashes exist. Standard Nix unpacking
enters the archive root, and the prebuilt executable is kept unchanged.

## Dynamic Hashes

Do not hand-edit release checksums in package metadata. The release workflow
downloads the release assets for the selected tag and runs:

```bash
packaging/scripts/update-release-metadata.sh <release-tag> <asset-dir>
```

That script recalculates package metadata from the actual release assets and
updates AUR, Winget, Homebrew, RPM, Debian, Chocolatey, Snap, Flatpak, Helm,
TrueNAS, Synology, and Nix release metadata before downstream publishing or
manual packaging runs. The Unraid Community Apps template at the repository
root intentionally tracks the floating `latest` tag instead of a pinned
release, so it never needs a post-release metadata commit.

The binary release matrix currently covers Linux GNU and musl on x86_64 and
aarch64, macOS on Intel and Apple Silicon, and Windows x64. Windows ARM64 is
not advertised or published until it has a native release runner and package
installer coverage.
