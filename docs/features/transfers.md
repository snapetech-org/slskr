# Transfers

slskR represents downloads and uploads as daemon-owned transfer records. Each
record moves through queue, start, progress, completion, cancellation, retry,
or failure state, and the Web UI and HTTP API expose the same transitions.

## Download and upload flows

- **Downloads** are queued from search results, browse views, or the API.
  slskR negotiates the peer connection, prefers type-1 obfuscated file
  transfer when the peer advertises it, falls back to a plain direct
  connection, and finally requests a server-mediated indirect connection.
- **Uploads** are served from the configured share index. Inbound transfer
  requests are accepted for indexed files and served over direct,
  peer-initiated, or indirect file-transfer sockets.
- **Resume** uses the peer's offset handshake where supported.
- **Retries** can be manual or handled by the auto-retry and rescue workers.

## Queue limits

| Setting | Default | Notes |
| --- | --- | --- |
| Combined active transfers | `520` | `SLSKR_TRANSFER_MAX_ACTIVE`; includes negotiation and inbound acceptance. Set `0` to block starts. |
| Upload slots | `20` | `SLSKD_UPLOAD_SLOTS`. |
| Download slots | `500` | `SLSKD_DOWNLOAD_SLOTS`. |
| In-memory transfer history | `500` | `SLSKR_TRANSFER_HISTORY_LIMIT`. |

`SLSKR_TRANSFER_ALLOW_INBOUND` and `SLSKR_TRANSFER_ALLOW_OUTBOUND` control
whether inbound serving and outbound downloads are allowed.

## Auto-retry

Failed audio downloads can be retried automatically while connected. The
worker is bounded by policy:

```toml
[transfers.auto_retry]
enabled = true
retry_delay_seconds = 1800
check_interval_seconds = 300
max_attempts = 5
max_files_per_cycle = 10
max_files_per_peer_per_cycle = 1
peer_cooldown_seconds = 900
alternate_sources_enabled = true
max_alternate_source_searches_per_cycle = 1
alternate_source_size_tolerance_percent = 5
```

Set `max_attempts = 0` for unlimited attempts during the process lifetime.

## Rescue

The rescue worker detects queued, low-throughput, and stalled audio attempts.
When an alternate is cached it atomically swaps sources; otherwise it issues
one bounded global search. It only acts on audio attempts and verifies
alternate sizes within the configured tolerance.

```toml
[transfers.rescue]
enabled = true
max_queue_time_seconds = 1800
min_throughput_kbps = 10
min_duration_seconds = 300
stalled_timeout_seconds = 120
check_interval_seconds = 45
retry_cooldown_seconds = 1800
max_files_per_cycle = 2
alternate_source_size_tolerance_percent = 5
```

Rescue can also use a verified multisource swarm when the exact hash metadata
and at least two usable range peers exist. A failed or stale swarm leaves the
original Soulseek attempt and partial file untouched.

## Completed-download layout

`SLSKR_DOWNLOAD_COMPLETED_PATH_TEMPLATE` controls the relative layout beneath
the state download root. Supported tokens are `{uploader}`, `{remote_folder}`,
`{remote_parent}`, `{remote_filename}`, `{batch_id}`, `{request_name}`, and
`{date}` or `{date:<chrono format>}`. An empty template preserves the remote
path. Explicit request destinations take precedence and remain confined.

## Multisource swarm

The explicit multisource API downloads from two or more HTTP range-capable
sources with an expected whole-file SHA-256 digest:

```bash
curl -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sources": ["https://example.test/a", "https://example.test/b"],
    "sha256": "<64-hex-digest>",
    "destination": "Artist/Album/Track.flac"
  }' \
  http://127.0.0.1:5030/api/v0/multisource/swarm
```

The daemon assigns bounded chunks across free sources, retries failed chunks
elsewhere, verifies the whole-file digest, and atomically publishes the
confined output. Ordinary Soulseek peers stay sequential because the network
has no harmless bounded range-cancellation primitive.

## Preview tickets

Short-lived peer and mesh preview tickets stream audio to the browser without
creating a normal download. Peer previews negotiate Soulseek directly and do
not write a local file. Mesh previews redeem a hash-pinned HTTP range source;
bytes are exposed only after exact-size and SHA-256 verification, and the
staging file is removed immediately afterward.

## API examples

```bash
# List grouped downloads
curl -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  http://127.0.0.1:5030/api/v0/transfers/downloads

# Queue downloads from one peer
curl -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"files":["Music/Artist/Album/Track.flac"]}' \
  http://127.0.0.1:5030/api/v0/transfers/downloads/<username>

# Start, report progress, and complete
curl -X POST -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  http://127.0.0.1:5030/api/v0/transfers/<id>/start
curl -X POST -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  -H "Content-Type: application/json" -d '{"bytes_transferred":1048576}' \
  http://127.0.0.1:5030/api/v0/transfers/<id>/progress
curl -X POST -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  http://127.0.0.1:5030/api/v0/transfers/<id>/complete
```

## See also

- [Shares and browse](shares-and-browse.md) for the files you serve.
- [Data and operations](data-and-operations.md) for persistence and history.
- [HTTP API reference](../http-api.md) for every transfer route.
