# Shares And Browse

slskR publishes configured local folders through a bounded share index and
lets you browse peers' shared files. The index uses virtual share paths, so
API and Web UI clients never see raw host paths.

## Share roots and scanning

Configure one or more roots in TOML or with the semicolon-separated
environment variable:

```toml
[shares]
dirs = ["/srv/slskr/shares/music"]
filters = ["\\.ini$", "Thumbs\\.db$", "\\.DS_Store$"]
follow_symlinks = false
include_hidden = false
scan_max_files = 250000
cache_tsv_enabled = true
```

```bash
SLSKR_SHARE_DIRS="/srv/music;/srv/audiobooks"
```

The daemon scans roots at startup and on demand. A rescan rebuilds the
in-memory index, replaces the durable SQLite `share_files` snapshot when
persistence is enabled, and rewrites the `share-index.tsv` compatibility cache.

### Safety limits

- `scan_max_files` defaults to **250,000** files.
- A scan that exceeds the filesystem-entry limit (`2,000,000`) or the
  pending-directory-path limit (`262,144`) fails without replacing the last
  complete index.
- Hidden files and symlinks are skipped unless explicitly enabled.
- Filters are regular expressions matched against the original local paths.

## Browse peers

Browse is tracked per peer. A request resolves the peer address, connects
directly or through the server-mediated indirect path, requests the share
list, and stores a bounded projection. Folder-level requests use
`FolderContentsRequest` for a single directory.

Browse states are `requested`, `partial`, `ready`, and `failed`. A partial
response is promoted to ready when a later response completes it.

## API examples

```bash
# Share status and rescan
curl -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  http://127.0.0.1:5030/api/v0/shares
curl -X POST -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  http://127.0.0.1:5030/api/v0/shares/rescan

# Catalog and per-root listing
curl -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  "http://127.0.0.1:5030/api/v0/shares/catalog?q=flac&limit=50"
curl -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  "http://127.0.0.1:5030/api/v0/files/music?folder=Artist/Album&limit=100"

# Browse a user and one folder
curl -X POST -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  http://127.0.0.1:5030/api/v0/users/<username>/browse/request
curl -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  http://127.0.0.1:5030/api/v0/users/<username>/browse
curl -X POST -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  -H "Content-Type: application/json" -d '{"folder":"Artist/Album"}' \
  http://127.0.0.1:5030/api/v0/users/<username>/browse/folder
```

## Limits

- The catalog and per-root listings support `q`, `prefix`, `folder`,
  `extension`, `recursive`, `limit`, and `offset` filters.
- Cached browse projections are bounded to 1,024 users and 10,000 file
  entries per user.
- Share APIs return virtual paths and per-root labels, not host paths.

## See also

- [Transfers](transfers.md) for downloading browsed files.
- [Configuration](../configuration.md) for share and scan settings.
- [HTTP API reference](../http-api.md) for exact query parameters.
