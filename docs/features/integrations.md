# Integrations

slskR integrates with Spotify, Lidarr, and an optional local visualizer. All
three are opt-in, and each reports an unavailable or disabled state when its
configuration is missing.

## Spotify

Spotify is the only integration with a full OAuth clickthrough. The callback
is served on the existing HTTP/Web UI port, so no second listener is needed.

```toml
[integrations.spotify]
enabled = true
client_id = "spotify-app-client-id"
# Optional; defaults to http://127.0.0.1:<http-port>/api/integrations/spotify/callback
# redirect_uri = "http://127.0.0.1:5030/api/integrations/spotify/callback"
```

Environment variables:

```bash
SLSKR_SPOTIFY_ENABLED=true
SLSKR_SPOTIFY_CLIENT_ID=spotify-app-client-id
# SLSKR_SPOTIFY_REDIRECT_URI=http://127.0.0.1:5030/api/integrations/spotify/callback
```

Register the redirect URI shown by the Web UI in the Spotify developer
dashboard. Authorization requests use a daemon-issued cryptographically random
state value that expires after **10 minutes**, is single-use, and is bounded to
**256** live pending states. Pending state persists through SQLite when
persistence is enabled so an authorization can survive a daemon restart until
it expires.

## Lidarr

Lidarr uses API-key authentication rather than OAuth. The Web UI provides a
configure, test, and sync flow: save the URL and API key, check system status,
preview wanted albums, then sync wanted items or request a manual import.

```toml
[integrations.lidarr]
enabled = true
url = "http://127.0.0.1:8686"
api_key = "lidarr-api-key"
```

```bash
SLSKR_LIDARR_ENABLED=true
SLSKR_LIDARR_URL=http://127.0.0.1:8686
SLSKR_LIDARR_API_KEY=lidarr-api-key
```

Unconfigured wanted/sync/import aliases fall back to local library state.

## Visualizer

The optional local visualizer launches an operator-provided command and records
launch attempts as events. Both settings are required:

```bash
SLSKR_EXTERNAL_VISUALIZER_COMMAND=/usr/local/bin/visualizer
SLSKR_EXTERNAL_VISUALIZER_LAUNCH_ENABLED=true
```

## Setup and boundaries

The [install runbook](../install.md#third-party-integrations) has the
step-by-step setup. Integrations are optional: search, transfers, shares,
messaging, and the core Web UI work without them. Their library, source, and
recommendation panels show unavailable or disabled states when configuration
or data is missing.

## See also

- [Configuration](../configuration.md) for the full option list.
- [Web UI and media](web-ui-and-media.md) for the integration screens.
- [App surface](../app-surface.md) for authorization and route details.
