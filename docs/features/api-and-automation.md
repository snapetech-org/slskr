# API And Automation

slskR is API-first: the Web UI uses the same versioned HTTP routes that
automation clients use. The maintained route and payload reference is the
[HTTP API reference](../http-api.md); the machine-readable contract is
[openapi.json](../openapi.json).

## Versioned routes and aliases

- Canonical routes live under `/api/v0/*`.
- Selected compatibility aliases preserve familiar paths and response shapes
  for existing automation.
- `GET /api/v0/capabilities` reports the supported surface, and
  `POST /api/v0/capabilities/negotiate` compares requested capabilities against
  the daemon's current set.

## Authentication

Protected routes accept `Authorization: Bearer <token>` or the
`X-API-Key: <token>` header. Distinct tokens can enforce roles:

| Token | Scope |
| --- | --- |
| `SLSKR_API_TOKEN` | Administrator; also signs short-lived administrator JWTs. |
| `SLSKR_API_READ_WRITE_TOKEN` | Non-administrator read/write. |
| `SLSKR_API_READ_ONLY_TOKEN` | Read-only. |
| `SLSKR_API_NOWPLAYING_TOKEN` | Scoped now-playing webhook only. |

Five failed source-IP or source-scoped credential attempts trigger a bounded
five-minute lockout. `DELETE /api/v0/session` revokes the presented JWT until
expiry. See [Security and access](security-and-access.md).

## Events

- `GET /api/v0/events` returns bounded records with `kind`, `topic`, `q`,
  `limit`, and `offset` filters.
- `GET /api/events/ws` streams `topic`, `type`, structured `data`, and
  `timestamp` frames.
- Event rows hydrate from and write through to SQLite when persistence is
  enabled.

## Webhooks

Create a webhook to receive signed delivery of selected events:

```bash
curl -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/slskr/webhook","events":"search.created,transfer.completed"}' \
  http://127.0.0.1:5030/api/webhooks
```

Creation returns the signing secret once. Deliveries sign
`<unix-timestamp>.<json-payload>` with HMAC-SHA256 in `X-Webhook-Signature`.
Receivers should verify the signature and reject timestamps more than five
minutes from their current time. Targets are validated against localhost,
private, loopback, link-local, documentation, multicast, and other blocked
ranges at registration and again at delivery after DNS resolution. See the
[Webhook API](../WEBHOOK_API.md).

## Batch operations

`POST /api/batch` runs multiple authenticated operations in one request, in
request order, with per-operation status and total timing. Batch bodies accept
native JSON values or pre-serialized JSON strings. A recommended batch size is
100 operations or fewer.

## Metrics and telemetry

- `GET /api/metrics` and `GET /api/v0/metrics` expose Prometheus-style
  counters and gauges.
- `GET /api/v0/stats` exposes compact aggregate counts.
- `GET /api/v0/telemetry` returns a protected JSON runtime health snapshot.

## Client libraries

| Language | Package | Guide |
| --- | --- | --- |
| TypeScript/JavaScript | `@slskr/api-client` | [client-ts/README.md](../../client-ts/README.md) |
| Python | `slskr` (async, Python 3.10–3.13) | [client-python/README.md](../../client-python/README.md) |
| Go | `github.com/snapetech/slskr/client-go` | [client-go/README.md](../../client-go/README.md) |
| Rust | Embedded `slskr-client` crate | [CLIENT_LIBRARIES.md](../CLIENT_LIBRARIES.md) |

```python
import asyncio
from slskr import SlskrClient

async def main():
    async with SlskrClient("http://127.0.0.1:5030", "your-api-token") as client:
        search = await client.create_search("beethoven symphony")
        details = await client.get_search_details(search["id"])
        print(len(details["results"]), "results")

asyncio.run(main())
```

Existing Python `slskd_api` automations can point at slskR with the daemon base
URL and API token; the compatibility surface covers the application, session,
server, search, transfer, room, conversation, user, share, file, relay,
options, event, log, and telemetry calls exercised by the local smoke suite.

## See also

- [HTTP API reference](../http-api.md) for routes and payloads.
- [Advanced API features](../http-api-features.md) for logging, batch, and
  WebSocket details.
- [HTTP API deployment](../http-api-deployment.md) for auth and exposure.
