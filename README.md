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

For local MCP access, see the [SnapeTech MCP integration guide](./docs/integrations/snapetech-mcp.md).

## Contents

- [Why slskR](#why-slskr)
- [Features](#features)
- [Get started](#get-started)
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

## Features

Each area has a focused guide with workflows, API examples, limits, and the
configuration that applies.

| Feature area | What you get | Guide |
| --- | --- | --- |
| Search and discovery | Global, user, room, and wishlist searches; result filters; discovery helpers. | [Search guide](./docs/features/search-and-discovery.md) |
| Transfers | Download/upload queue, resume, retry, rescue, path templates, multisource swarm, previews. | [Transfers guide](./docs/features/transfers.md) |
| Shares and browse | Bounded share index, regex filters, virtual paths, catalog, peer browse. | [Shares guide](./docs/features/shares-and-browse.md) |
| Messaging, rooms, and users | Private messages, rooms, watched users, contacts, notes, interests, bans. | [Messaging guide](./docs/features/messaging-rooms-users.md) |
| Web UI and media | Shipped React UI, player, previews, collections, share groups, listening parties. | [Web UI guide](./docs/features/web-ui-and-media.md) |
| Integrations | Spotify, Lidarr, and the optional visualizer. | [Integrations guide](./docs/features/integrations.md) |
| Mesh, DHT, and pods | DHT rendezvous, TLS/QUIC mesh, pods, channels, room bindings, Gold Star Club. | [Mesh guide](./docs/features/mesh-dht-pods.md) |
| API and automation | Versioned routes, auth, events, webhooks, batch, metrics, typed clients. | [API guide](./docs/features/api-and-automation.md) |
| Data and operations | SQLite persistence, database maintenance, logs, metrics, telemetry. | [Operations guide](./docs/features/data-and-operations.md) |
| Security and access | Bind defaults, tokens, CSRF, rate limits, webhook policy, reverse proxies. | [Security guide](./docs/features/security-and-access.md) |
| Localization | Twelve UI locales, English fallback, locale-aware formatting. | [Localization guide](./docs/features/localization.md) |
| Performance | Measured CPU and memory evidence, methods, and limits. | [Performance analysis](./docs/performance-analysis.md) |

Also included:

- Global, user, room, and scheduled wishlist searches with result filters,
  duplicate folding, hidden/blocked-user handling, and metadata-assisted
  follow-ups.
- Auto-retry and rescue workers for failed, queued, slow, or stalled audio
  downloads, with bounded alternate-source searches.
- Offset/resume, type-1 obfuscated and indirect peer fallback, completed-path
  templates, and hash-verified multisource swarms.
- Share catalog, per-root file listing, peer browse, folder browse, and partial
  browse state.
- Private-message acknowledgements, room join/leave, watched-user stats,
  contacts, notes, liked/hated interests, and username/IP bans.
- Collections, share groups, playlist intake, player controls, local and peer
  previews, and listening parties.
- Spotify OAuth, Lidarr status/wanted/import, and a local visualizer hook.
- Mainline DHT, TLS mesh transport, QUIC control/data, pods, member-only
  channels, Soulseek-room bindings, hash metadata, and shadow-index discovery.
- Versioned `/api/v0/*` routes, OpenAPI, bearer and `X-API-Key` auth, scoped
  tokens, WebSocket events, webhooks, batch operations, and metrics/telemetry.
- TypeScript, Python, Go, and Rust clients.
- Optional SQLite persistence, database cleanup/vacuum, runtime log levels, and
  health checks.
- Loopback-first defaults, CSRF checks, rate limits, SSRF-resistant webhook
  targets, and OS keyring, systemd, file, memory, or env credential stores.
- Twelve interface locales with English fallback and locale-aware date, number,
  and byte formatting.

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

## Feature maturity

The stable baseline is the Soulseek client, Web UI, REST API, and ordinary
single-source transfers. Optional features such as persistence, integrations,
mesh, DHT, pods, and multisource downloads need configuration or suitable
peers. See [Status and support boundaries](./docs/status.md), the
[feature map](./docs/FEATURES.md), and the
[feature guides](./docs/features/README.md).

## Project status and contribution

- [Documentation index](./docs/README.md)
- [Feature guides](./docs/features/README.md)
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
