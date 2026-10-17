# Security And Access

slskR defaults to a loopback-only listener and authentication on. This guide
covers the credentials, tokens, browser protections, and exposure rules you
need before putting the daemon on a network.

## Bind and authentication defaults

- HTTP binds to `127.0.0.1:5030` by default.
- Authentication is required by default.
- The Web UI signs in with the web-auth username and password. The default is
  username `slskr`, password `slskr`; change it before exposing the daemon.
- `SLSKR_AUTH_DISABLED=true` explicitly disables API authentication and is only
  appropriate on an isolated, trusted network.

```toml
[auth]
username = "operator"
password = "use-a-secret-manager"
```

```bash
SLSKD_USERNAME=operator
SLSKD_PASSWORD=use-a-secret-manager
```

The `SLSKD_` names are the retained web-login variable names. Soulseek account
credentials use `SLSK_USERNAME` and `SLSK_PASSWORD`.

## API tokens

| Variable | Role |
| --- | --- |
| `SLSKR_API_TOKEN` | Administrator; also signs short-lived administrator JWTs. |
| `SLSKR_API_READ_WRITE_TOKEN` | Non-administrator read/write. |
| `SLSKR_API_READ_ONLY_TOKEN` | Read-only. |
| `SLSKR_API_NOWPLAYING_TOKEN` | Scoped now-playing webhook only. |

Protected routes accept `Authorization: Bearer <token>` or `X-API-Key: <token>`.
Keep tokens in memory or session storage; do not embed long-lived tokens in
browser storage or shared URLs. Five failed source-IP or source-scoped
credential attempts trigger a bounded five-minute lockout.

## Browser protections

- Unsafe API methods reject cross-site browser requests with foreign `Origin`
  or `Referer` headers.
- Sanitized config responses never return credentials.
- Share APIs return virtual paths, not raw host paths.
- API rate limits default to **1,000** anonymous and **5,000** authenticated
  requests per window (`SLSKR_API_RATE_LIMIT_ANONYMOUS`,
  `SLSKR_API_RATE_LIMIT_AUTHENTICATED`).

## Webhook policy

Webhook targets are validated at registration and again at delivery after DNS
resolution. Localhost, private, loopback, link-local, documentation,
multicast, and other blocked ranges are rejected by default. Operators can
extend the policy:

```bash
SLSKR_WEBHOOK_DENY_CIDRS=203.0.113.0/24
SLSKR_WEBHOOK_ALLOW_CIDRS=198.51.100.10/32
```

## Credential storage

Soulseek credentials can live in the platform OS keyring, systemd credentials,
process memory, a restricted local file, or environment/config values. See
[Credential storage](../credential-storage.md) for the tradeoffs and systemd
examples.

## Reverse proxy and remote access

Terminate TLS at a proxy you control and forward to the loopback-bound daemon.
Preserve `Host`, `Origin`, `Referer`, and forwarding headers, and set
`SLSKR_TRUSTED_PROXY_CIDRS` for every trusted proxy CIDR. Do not expose the
HTTP listener directly to the public internet. See
[HTTP API deployment](../http-api-deployment.md).

## See also

- [Configuration](../configuration.md) for auth and rate-limit settings.
- [Credential storage](../credential-storage.md) for secret handling.
- [Compliance](../../COMPLIANCE.md) for public posture and licensing notes.
