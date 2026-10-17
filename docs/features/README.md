# Feature Documentation

This directory explains slskR's user-facing feature areas: what each one does,
how to use it from the Web UI and HTTP API, and the configuration or limits
that apply. For the canonical route and payload reference, see the
[HTTP API reference](../http-api.md). For which surfaces are stable versus
configuration-dependent, see [Status and support boundaries](../status.md).

| Area | Guide | What it covers |
| --- | --- | --- |
| Search and discovery | [search-and-discovery.md](search-and-discovery.md) | Global, user, room, and wishlist searches; result review; filters; discovery helpers. |
| Transfers | [transfers.md](transfers.md) | Download/upload queue, resume, retry, rescue, path templates, multisource swarm, previews. |
| Shares and browse | [shares-and-browse.md](shares-and-browse.md) | Share roots, scanning, filters, virtual paths, catalog, peer browse. |
| Messaging, rooms, and users | [messaging-rooms-users.md](messaging-rooms-users.md) | Private messages, rooms, watched users, contacts, notes, interests, bans. |
| Web UI and media | [web-ui-and-media.md](web-ui-and-media.md) | Shipped React UI, player, previews, collections, share groups, listening parties. |
| Integrations | [integrations.md](integrations.md) | Spotify, Lidarr, and the visualizer. |
| Mesh, DHT, and pods | [mesh-dht-pods.md](mesh-dht-pods.md) | DHT rendezvous, TLS/QUIC mesh, pods, channels, room bindings, Gold Star Club. |
| API and automation | [api-and-automation.md](api-and-automation.md) | Versioned routes, auth, events, webhooks, batch operations, clients. |
| Data and operations | [data-and-operations.md](data-and-operations.md) | SQLite persistence, database maintenance, logs, metrics, telemetry. |
| Security and access | [security-and-access.md](security-and-access.md) | Bind defaults, tokens, CSRF, rate limits, webhook policy, reverse proxies, credential storage. |
| Localization | [localization.md](localization.md) | Supported UI locales, fallback, and formatting behavior. |
| Performance | [../performance-analysis.md](../performance-analysis.md) | Measured CPU and memory evidence, methods, and limits. |

## How to read these guides

- **Available now** means the workflow is implemented in the Rust runtime and
  works with a normal account and network setup.
- **Needs configuration** means the UI or API surface exists but requires a
  setting, an external service, or suitable peers.
- **Compatibility surface** means a familiar route or response shape is
  preserved for automation, but it is not a durable slskR feature by itself.

The [status guide](../status.md) is the authoritative summary of those
boundaries. Feature-specific setup details live in the guides above and in the
[configuration reference](../configuration.md).
