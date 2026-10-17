# Messaging, Rooms, And Users

slskR keeps private-message conversations, room state, watched users, and
social projections in the daemon so the Web UI and API see one consistent
view. With SQLite persistence enabled, those projections survive restarts.

## Private messages

- Send, record inbound messages, list the newest projections, read one user's
  history, and acknowledge messages.
- The in-memory projection keeps the newest **500** messages; persisted
  storage remains durable beyond that window.
- Acknowledgement is forwarded to the server when connected.

```bash
curl -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","body":"Hello"}' \
  http://127.0.0.1:5030/api/v0/messages

curl -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  "http://127.0.0.1:5030/api/v0/messages?username=alice&limit=50"

curl -X POST -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  http://127.0.0.1:5030/api/v0/messages/<id>/ack
```

## Rooms

- List up to **1,024** room projections with joined state, room kind, user
  count, operated flag, message count, up to **10,000** projected members, and
  the latest **1,000** projected messages per room.
- Join and leave rooms, refresh the server room list, and send room messages.
- Joined-room subscriptions and message projections persist when persistence
  is enabled.

```bash
curl -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  "http://127.0.0.1:5030/api/v0/rooms?joined=true"

curl -X POST -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  http://127.0.0.1:5030/api/v0/rooms/<room>/join

curl -X POST -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"slskr","body":"Hello room"}' \
  http://127.0.0.1:5030/api/v0/rooms/<room>/messages
```

## Watched users and stats

Watch or unwatch a user, request server user stats, and keep bounded user
projections with average speed, upload count, file count, and directory count.
The projection list is capped at **4,096** users.

```bash
curl -X POST -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  -H "Content-Type: application/json" -d '{"username":"alice"}' \
  http://127.0.0.1:5030/api/v0/users/watch

curl -X POST -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  http://127.0.0.1:5030/api/v0/users/alice/stats/request
```

## Contacts, notes, interests, and bans

The daemon also maintains:

- **Contacts** and discovery/invite helpers.
- **User notes** with create, update, and delete.
- **Liked and hated interests** used by recommendation views.
- **Username and IP bans** used by security dashboards.

These projections write through to SQLite when persistence is enabled.

## Rooms, pods, and DMs

Pod channel messages and Soulseek-room bindings are separate from ordinary
Soulseek rooms. A `readonly` or `mirror` binding bridges a pod channel to a
live Soulseek room, and `soulseek-dm:` channels project through the durable
private-message conversation. See [Mesh, DHT, and pods](mesh-dht-pods.md).

## See also

- [Web UI and media](web-ui-and-media.md) for the chat and room screens.
- [Data and operations](data-and-operations.md) for persistence.
- [HTTP API reference](../http-api.md) for every social route.
