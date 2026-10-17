# Web UI And Media

`slskr serve` hosts the bundled React Web UI, the HTTP API, and the WebSocket
event feed on one listener. The UI is the primary operator surface; the API is
the automation surface.

## Shipped UI

The production bundle lives in `web/` and is served from `/`. It covers:

- Search, result review, wishlist, and discovery views.
- Downloads and uploads with progress, retry, cancel, and history.
- Rooms, private messages, users, contacts, and browse.
- Shares, collections, share groups, and shared-with-me views.
- Integrations, system state, telemetry, metrics, logs, and preferences.
- Player controls, local and peer previews, library and source views,
  recommendations, and listening-party workflows.

Media and discovery panels report unavailable or disabled states when their
configuration, local data, or peers are missing.

## Player and previews

The player streams audio through short-lived preview tickets. Peer previews
negotiate Soulseek directly and do not create a local file. Mesh previews
redeem a hash-pinned HTTP range source and expose bytes only after exact-size
and SHA-256 verification. Completed downloads can also be played from the
local library view.

## Collections and share groups

Collections group library items for sharing and playback; share groups group
users for grant workflows. Both are bounded, persist through SQLite when
enabled, and are exposed through the API as well as the UI.

## Build and run the UI

```bash
npm --prefix web ci
npm --prefix web run build
slskr serve
```

`slskr serve` looks for the production UI in `SLSKR_WEB_BUILD_DIR`, next to the
binary as `web/build`, under `$prefix/share/slskr/web/build`, or in the current
checkout. If no built UI is present, `/` falls back to the built-in operator
dashboard and explains how to install the full UI.

## Rust/WASM migration target

`crates/slskr-web` is a separate Rust/WASM shell used to migrate routes one at
a time. It is **not** the shipped bundle. The React app remains production
until a Rust route reaches parity, has matching tests, and passes browser
verification. See [Rust Web UI Migration](../rust-web-ui.md) and the
[Web UI README](../../web/README.md).

## Screenshots

The README screenshots are generated from the local UI with mocked daemon
responses:

- [Search and discovery](../screenshots/webui-searches.png)
- [Transfers](../screenshots/webui-downloads.png)
- [Rooms and messaging](../screenshots/webui-rooms.png)
- [System status](../screenshots/webui-system.png)

## See also

- [Localization](localization.md) for the interface-language selector.
- [API and automation](api-and-automation.md) for the same surfaces over HTTP.
- [Web UI README](../../web/README.md) for development and audit workflows.
