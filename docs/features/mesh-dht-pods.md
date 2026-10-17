# Mesh, DHT, And Pods

The native/current runtime includes Mainline-DHT rendezvous, TLS mesh
transport, QUIC control/data paths, private service gateways, pods, and
content-hash discovery. These are optional, configuration-dependent systems:
their presence in the UI or API does not mean they are enabled or that every
peer will interoperate.

## Shared peer port

In native/current operation, one numeric peer port carries:

- ordinary Soulseek peer traffic and type-1 obfuscation on **TCP**;
- DHT, mesh control, and QUIC on **UDP**.

The default peer port is **50300**. A custom `[network].listen_port` (or
`SLSK_LISTEN_PORT`) is projected across the peer services. Do not configure a
separate public DHT/mesh/QUIC port in this profile. The frozen compatibility
profile keeps its historical listener behavior.

## DHT

DHT is enabled by default in native/current operation:

```toml
[dht]
enabled = true
# port = 50300
```

```bash
SLSKR_DHT_ENABLED=true
```

The client refreshes and announces the frozen `slskdn-mesh-v1` primary and
backup rendezvous keys on a bounded interval. `GET /api/dht/status` reports
bootstrap, routing, public-address, firewall, announce, lookup, and
discovered-beacon state.

## Mesh transport

- Pinned TLS 1.3 overlay client and server paths use bounded `SLSKDNM1`
  framing over the shared peer TCP listener.
- The gateway stores `overlay-certificate.der`, `overlay-private-key.der`, and
  `peer-capability-key.bin` identity files.
- `GET /api/mesh/transport` exposes the certificate SHA-256 fingerprint for pod
  policy pinning.
- QUIC control and data paths use the shared UDP port.
- Inbound mesh calls require a fresh Soulseek-authenticated capability and a
  matching peer IP. slskR peers additionally sign the overlay hello with their
  durable capability key and bind it to the gateway certificate.

## Pods and channels

Pods are bounded durable definitions and memberships stored in `pods.json`.
Channel history is stored in `pod-channel-messages.json` with stable message
IDs and incremental `since` cursors.

- `GET/POST /api/v0/pods`, `GET/PUT/DELETE /api/v0/pods/:podId`, and member
  action routes manage pods and membership.
- Private pod reads require membership; mutations require owner/moderator or
  self-service authority.
- Channel messages are member-only and bounded.
- `readonly` and `mirror` bindings connect a pod channel to a live Soulseek
  room; `soulseek-dm:` channels project through the private-message store.

```bash
curl -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  http://127.0.0.1:5030/api/v0/pods

curl -H "Authorization: Bearer $SLSKR_API_TOKEN" \
  "http://127.0.0.1:5030/api/v0/pods/<podId>/channels/<channelId>/messages?since=0"
```

## Content-hash and shadow-index discovery

The daemon keeps a bounded content-discovery store that resolves exact size
plus `byteHash`, `fullFileHash`, or `fileSha256` metadata to MusicBrainz
recording IDs and shadow-index peer IDs.

- `GET /api/v0/hashdb/stats`, `/entries`, `/hash/:flacKey`, and
  `/hash/by-size/:size` inspect the hash registry.
- `POST /api/v0/hashdb/hash` and `/sync/merge` merge exact-size SHA-256
  metadata.
- `POST /api/v0/virtualsoulfind/shadow-index/sync/merge` and
  `GET /api/v0/virtualsoulfind/shadow-index/:recordingId` maintain the
  recording-to-peer relation used by source-less multisource swarms.

`byteHash` alone is never treated as a whole-file digest. The overlay
`shadow-index` service returns only frozen-compatible aggregate variant
counts; `MeshContent` performs the subsequent pinned exact-range byte fetch.

## Trust records

The frozen capability wire omits the certificate pin and range URL, so
operators can configure bounded peer-ID, username, endpoint, and pin trust
records with optional range URL templates. Source-less swarms can then select
trusted or slskR-local HTTP range endpoints, and preview tickets can fetch
exact verified ranges through a trusted peer's `MeshContent` overlay.

## Gold Star Club

The Gold Star Club is a reserved PodCore community and testing pod, not a
download entitlement or account tier. It is opt-in in native/current
operation, capped at **250** active members, and leaving is a local,
irreversible opt-out. Read [Gold Star Club](../gold-star-club.md) before
enabling it.

```toml
[podcore.gold_star_club]
autojoin = false
```

```bash
SLSKR_POD_GOLD_STAR_CLUB_AUTOJOIN=false
```

## Maturity

DHT, mesh, pods, shadow index, and multisource downloads are distinct
experimental or configuration-dependent systems. Their presence in the UI,
API, or configuration does not guarantee enablement, interoperability, or
production suitability in every setup. See [Status and support boundaries](../status.md)
and [Mesh, Pod, and Service-Fabric Compatibility](../app-surface.md#mesh-pod-and-service-fabric-compatibility).

## See also

- [Transfers](transfers.md) for multisource swarms and previews.
- [Search and discovery](search-and-discovery.md) for content-hash discovery.
- [Architecture](../architecture.md) for the listener layout.
