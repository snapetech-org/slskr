# Search And Discovery

slskR can search the Soulseek network globally, target a single user, target a
room, or run scheduled wishlist searches. Results are stored as bounded search
records that the Web UI and API can page, filter, and prune.

## Search targets

| Target | Required field | Behavior |
| --- | --- | --- |
| `global` | none | Sends the query to the network and merges peer responses. |
| `user` | `username` | Targets one peer's shared files. |
| `room` | `room` | Targets the members of one room. |
| `wishlist` | none | Runs from saved wishlist items on a schedule. |

## Create and review a search

From the Web UI, open **Search**, enter a query, choose a target, and start the
search. Results show filename, size, extension, peer username, slot state,
average speed, and queue length where the peer provides them.

From the API:

```bash
curl -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"Example sound file Ogg Vorbis","target":"global"}' \
  http://127.0.0.1:5030/api/v0/searches
```

Read and manage records:

```bash
curl -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  "http://127.0.0.1:5030/api/v0/searches?status=active&limit=20"

curl -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  http://127.0.0.1:5030/api/v0/searches/<token>

curl -X POST -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  http://127.0.0.1:5030/api/v0/searches/<token>/complete
```

## Limits and timing

- Each search record retains at most **10,000 file results**.
- Active searches expire after **15 seconds** without a peer response. Each
  response resets the inactivity window.
- Scheduled wishlist searches use an explicit **five-minute** window.
- `POST /api/v0/searches/prune` expires due searches and removes old records.

## Filters and result review

The Web UI adds result filters, duplicate folding, hidden/blocked-user
handling, search history, review notes, acquisition profiles, and
metadata-assisted follow-up searches. Server-side search-request filters are
configured in the TOML config:

```toml
[filters.search]
# Drop incoming search requests matching any expression.
request = ["^.{1,2}$"]
```

See the annotated [config example](../slskr.config.example.toml) for the full
option set.

## Wishlist and discovery

Wishlist items are managed through the `/api/wishlist` routes and the Web UI,
including CSV import and release-radar/source-feed helpers. The daemon can run
wishlist searches in the background while connected.

Discovery helpers build on the same result data:

- **Metadata-assisted searches** use local metadata to refine follow-up
  queries.
- **Discovery graph panels** show how results, peers, and saved items relate.
- **Content-hash discovery** resolves exact size plus a whole-file digest to
  MusicBrainz recording IDs and shadow-index peers; see
  [Mesh, DHT, and pods](mesh-dht-pods.md) for the hash and shadow-index APIs.

## See also

- [Transfers](transfers.md) for downloading a result.
- [HTTP API reference](../http-api.md) for every search route and payload.
- [Feature map](../FEATURES.md) for the product-level overview.
