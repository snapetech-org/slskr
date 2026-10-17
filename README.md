<h1 align="center">slskR</h1>
<p align="center"><strong>A fast, lightweight Rust daemon and web UI for Soulseek file sharing</strong></p>
<p align="center">
  <a href="https://github.com/snapetech-org/slskr/releases">Releases</a> ·
  <a href="https://github.com/snapetech-org/slskr/issues">Issues</a> ·
  <a href="./docs/README.md">Documentation</a> ·
  <a href="https://discord.gg/5PyXBfvS6T">Community</a>
</p>

slskR is a self-hosted Soulseek client written in Rust. It ships a daemon, a
REST API, and a bundled web UI together. It is an independent implementation
with its own configuration and release contracts, not a fork or wrapper.

## Contents

- [Why slskR](#why-slskr)
- [Get started](#get-started)
- [Use the main workflows](#use-the-main-workflows)
- [Feature maturity](#feature-maturity)
- [Project status and contribution](#project-status-and-contribution)
- [Support](#support)
- [License](#license)

## Why slskR

- **Substantially lighter than the upstream client.** In a matched idle
  benchmark, slskR used about **16x less CPU time** and **85–89% less memory**.
  A separate connected-idle run measured about **30x less CPU time** and
  **85–95% less memory**. See the
  [performance analysis](./docs/performance-analysis.md) and the
  [connected-idle report](./benchmarks/artifacts/20261012-live-soulseek-idle.md).
- **One process for the daemon, API, and UI.** No sidecar or external web host.
- **API-first.** Versioned `/api/v0/*` routes, OpenAPI, WebSocket events,
  webhooks, and TypeScript, Python, and Go clients.
- **Safe defaults.** Loopback-only HTTP, authentication on by default, CSRF
  checks, virtual share paths, and scoped API tokens.
- **Runs anywhere.** Linux, macOS, Windows, Docker, Kubernetes, Unraid,
  TrueNAS, Synology, and the major package managers.

## Get started

- [Install and configure slskR](./docs/getting-started.md)
- [Configuration reference](./docs/configuration.md)
- [Container deployment](./docs/install.md#container-shape)
- [Troubleshooting](./docs/troubleshooting.md)
- [Build from source](./docs/install.md#build)

### Docker

```bash
SLSKR_API_TOKEN="$(openssl rand -hex 32)"
SLSKD_PASSWORD="$(openssl rand -hex 16)"

docker run -d --name slskr --restart unless-stopped \
  -p 5030:5030 -p 2234:2234/tcp -p 2234:2234/udp \
  -e SLSKR_API_TOKEN="$SLSKR_API_TOKEN" \
  -e SLSKD_PASSWORD="$SLSKD_PASSWORD" \
  -v slskr-state:/var/lib/slskr \
  ghcr.io/snapetech/slskr:latest
```

Open <http://localhost:5030/>, sign in as `slskr` with the generated password,
then enter your Soulseek credentials.

### Release binary

Download the archive for your platform from
[Releases](https://github.com/snapetech-org/slskr/releases), verify it against
`SHA256SUMS.txt`, extract it, and put `slskr` on your `PATH`:

```bash
tar -xzf slskr-<version>-<target>.tar.gz
sudo install -Dm755 slskr /usr/local/bin/slskr
slskr serve
```

## Use the main workflows

- [Search and discovery](./docs/getting-started.md#4-run-a-search-and-download) —
  search globally, by user, or in rooms; review results and browse peers.
- [Transfers](./docs/FEATURES.md#transfers-and-content-discovery) — queue,
  resume, retry, and track downloads and uploads.
- [Shares and browse](./docs/FEATURES.md#soulseek-client) — publish a bounded
  index of your library through virtual paths.
- [Messages and rooms](./docs/FEATURES.md#soulseek-client) — chat, join rooms,
  watch users, and manage contacts.
- [Web UI and media](./docs/FEATURES.md#web-ui-and-media-workflows) — player
  controls, previews, library views, and listening parties.
- [Integrations](./docs/install.md#third-party-integrations) — Spotify, Lidarr,
  and visualizer workflows.
- [HTTP API and clients](./docs/http-api.md) — REST routes, OpenAPI, events,
  webhooks, and SDKs.
- [System settings](./docs/configuration.md) — credentials, ports, logging,
  metrics, and persistence.

## Feature maturity

The stable baseline is the Soulseek client, Web UI, REST API, and ordinary
single-source transfers. Optional features such as persistence, integrations,
mesh, DHT, pods, and multisource downloads need configuration or suitable
peers. See [Status and support boundaries](./docs/status.md) and the
[feature map](./docs/FEATURES.md).

## Project status and contribution

- [Documentation index](./docs/README.md)
- [Architecture](./docs/architecture.md)
- [Testing and live interop](./docs/live-interop-test-matrix.md)
- [Release channels](./docs/dev/release-channels.md)
- [API reference](./docs/http-api.md)

slskR is an independent Rust implementation. It pursues compatibility with
useful Soulseek workflows but is not a fork of any other client.

## Support

- [Discord](https://discord.gg/5PyXBfvS6T)
- [Issues](https://github.com/snapetech-org/slskr/issues)
- [Ko-fi](https://ko-fi.com/snapetech)

## License

GNU Affero General Public License v3.0. See [LICENSE](./LICENSE) and
[NOTICE](./NOTICE).
