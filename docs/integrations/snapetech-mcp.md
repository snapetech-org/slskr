# SnapeTech MCP

slskR does not run an MCP server inside the application. The shared
`snapetech-mcp` process connects to this instance over its existing REST API
using MCP stdio transport. Its quickstart is in the sibling
`snapetech-mcp/README.md`.

## Tools and API access

| MCP tool | slskR endpoint | Result |
| --- | --- | --- |
| `slskr_status` | `GET /api/health` | Reachability only. |
| `slskr_get_transfer_summary` | `GET /api/v0/stats` | Aggregate transfer/share counts and upload/download rates. |
| `slskr_list_transfers` | `GET /api/transfers` | A page of transfer state, progress, size, and rate. |

Configure `SNAPETECH_MCP_APPS=slskr`,
`SNAPETECH_MCP_SLSKR_URL=<slskR base URL>`, and
`SNAPETECH_MCP_SLSKR_API_KEY=<read-only token>` in the MCP host's protected
environment. Set the value from `SLSKR_API_READ_ONLY_TOKEN`; the bridge sends
it as `Authorization: Bearer`. The base URL is the application origin.

## Security

Use the read-only token, keep authentication enabled, and retain slskR's
loopback-only listener unless a trusted reverse proxy terminates TLS and is
configured as trusted. Replace the default `slskr/slskr` web login before
network exposure. Do not use the administrator or read/write API token for this
bridge.

The transfer tool omits filenames, virtual paths, peer names, and hashes. Keep
the MCP process attached to a trusted local client; never expose its stdio
transport through a TCP bridge or reverse proxy.

## Competitor feature coverage

Nicotine+ and slskd establish the mainstream Soulseek client surface: search, peer
browsing and shares, downloads/uploads, chats/rooms, and user presence. slskR's own
feature map adds global/user/room/wishlist search, bounded share browsing, rich transfer
recovery, media workflows, automation, and experimental mesh/pod features. See
[Nicotine+](https://nicotine-plus.org/), [slskd](https://github.com/slskd/slskd), and the [slskR feature map](../../README.md#features).

Snapetech MCP exposes aggregate transfer/share statistics and a bounded page of transfer
state. It omits usernames, search terms, filenames, virtual paths, and peer records.
Search still contacts peers, and raw results can expose identities and remote filenames;
peer browsing, messages, downloads, retries, and other controls need a separate
authorization and side-effect review.

**Confidence:** high for the product feature inventory from primary project documentation; moderate for direct feature comparison because peer search, mesh, and automation workflows differ from the safe MCP read surface.

Source contract: `docs/features/security-and-access.md`,
`docs/features/api-and-automation.md`, and the transfer API route
implementation.
