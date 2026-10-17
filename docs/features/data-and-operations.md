# Data And Operations

slskR keeps configuration, state, and optional persistence in the state
directory. This guide covers what is stored, how to maintain it, and the
runtime signals operators use to monitor a deployment.

## State directory

| Path | Contents |
| --- | --- |
| `$SLSKR_STATE_DIR` | Messages, transfer state, share indexes, SQLite data, and durable mesh identity. |
| `$STATE_DIR/downloads` | Completed downloads by default. |
| `$STATE_DIR/incomplete` | In-progress downloads by default. |
| `$STATE_DIR/share-index.tsv` | Optional compatibility/debug share mirror. |
| `$STATE_DIR/transfer-state.json` | Reloadable transfer projection. |
| `$STATE_DIR/content-discovery-state.json` | Hash and shadow-index discovery metadata. |
| `$STATE_DIR/pods.json` | Pod definitions and membership. |
| `$STATE_DIR/pod-channel-messages.json` | Pod channel history. |

On Unix, the state directory must be a real directory, not a symlink, and
slskR tightens it to mode `0700`. Back up the whole state directory together
with the config file; the SQLite database and JSON files are related.

## SQLite persistence

Persistence is **off by default**:

```toml
[persistence]
enabled = true
```

```bash
SLSKR_PERSISTENCE_ENABLED=true
```

When enabled, share indexes, events, searches, transfers, users, browse,
messages, rooms, collections, library items, destinations, now-playing,
wishlist, contacts, share groups, share grants, user notes, interests,
security bans, OAuth state, webhooks, and runtime compatibility projections
write through to SQLite. Transfer projection state also remains restart-safe
through `transfer-state.json`.

## Database maintenance

```bash
# Counts and health
curl -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  http://127.0.0.1:5030/api/v0/database/stats

# Remove persisted messages older than 30 days and prune terminal transfers
curl -X POST -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  -H "Content-Type: application/json" -d '{"days":30}' \
  http://127.0.0.1:5030/api/v0/database/cleanup

# Reclaim space
curl -X POST -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  http://127.0.0.1:5030/api/v0/database/vacuum
```

Cleanup and vacuum return a structured skipped status when persistence is
disabled.

## Logs

- `SLSKR_LOG_LEVEL` accepts `trace`, `debug`, `info`, `warn`, or `error`.
  `RUST_LOG` is accepted as a familiar alias; `SLSKR_LOG_LEVEL` takes
  precedence.
- The System → Logs tab can inspect recent logs and change the runtime level
  without a restart.
- HTTP request logs are written to stderr with method, path, status, bytes, and
  duration.

## Metrics and telemetry

- `GET /api/metrics` and `GET /api/v0/metrics` expose Prometheus-style
  counters and gauges for sessions, listeners, shares, searches, users, browse,
  messages, rooms, transfers, runtime operations, and persisted row counts.
- `GET /api/v0/stats` exposes compact aggregate counts.
- `GET /api/v0/telemetry` returns a protected JSON runtime health snapshot with
  sanitized config flags, listener/session state, storage status, database
  health, and projection counts.
- `GET /health` is a lightweight health check; `/health/mesh` reports mesh
  health.

## Upgrade and backup checklist

1. Stop the daemon or accept a quiescent snapshot.
2. Copy the config file and the entire state directory.
3. Keep the SQLite database and the JSON state files together.
4. Start the new version and check `/health`, `/api/v0/stats`, and the System
   page.
5. Keep the previous state copy until the new version has run successfully.

## See also

- [Configuration](../configuration.md) for every setting.
- [Install runbook](../install.md) for service and container layouts.
- [App surface](../app-surface.md) for the database and telemetry routes.
