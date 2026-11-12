# slskd vs slskr: downloads, uploads, and connection/network setup

Research date: 2026-11-12

This document compares slskd and slskr at the source level for:

- connection establishment, listeners, peer dialing, obfuscation, timeouts and reconnect behavior;
- the download lifecycle (admission, negotiation, transfer, retry, resume);
- the upload lifecycle (admission, queueing, slots, transfer, completion);
- the "legacy outbound" claims introduced by PR #214
  (`fix/transfers-slskd-parity`, fork `ramonskie/slskr`).

It is a comparison of behavior, not a feature scorecard. Where the PR's wording is
inaccurate, this document says so explicitly and proposes corrected wording.

## 0. Versions examined

| Project | Revision | Notes |
| --- | --- | --- |
| slskr | `56df32a3` on `fix/transfers-slskd-parity` | Includes the six PR #214 commits; base `e7e2430107b52587e54f5327198fb9a4fb73a533` |
| slskd | `2622c9b6`, `0.26.2-125-g2622c9b6` | 2026-11-08 |
| Soulseek.NET | `10f2c46` | Dependency of slskd: `Soulseek` `10.0.2` (`src/slskd/slskd.csproj:73`) |
| Nicotine+ | `5b76828` | Used as the third-party protocol reference, not as a comparison target |

The slskr side is the PR branch, not `main`; the download negotiation described here
(QueueUpload-first) is not the behavior of the base commit.

Method: static review of the checked-out trees, with Nicotine+ used as an independent
protocol reference. The slskd and Nicotine+ behaviors cited below are read directly from
their handlers and message definitions; line numbers refer to the revisions in the table
above and will drift as those projects change.

## 1. Executive summary

1. **Both projects delegate almost everything below "application policy" to different
   client stacks.** slskd is an ASP.NET Core application on top of Soulseek.NET.
   slskr is a Rust daemon with its own `slskr-client` / `slskr-protocol` crates and a
   set of runtime owners. Transfer semantics therefore diverge mostly at the
   negotiation and queueing layer, not at the wire-format layer.

2. **The modern download request is `QueueUpload` (peer code 43).** It is what
   Nicotine+ >= 3.0.3, Museek+ and the official clients send. The uploader answers
   later with `TransferRequest { direction: 1 }` and then dials the downloader.
   PR #214's move of slskr's normal download path to `QueueUpload` is directionally
   correct.

3. **The legacy `TransferRequest { direction: 0 }` flow is not "silently ignored by
   current peers".** That statement in `crates/slskr/src/file_transfer_runtime_owners/
   peer_negotiation.rs:381` does not hold up against three facts:
   - slskd/Soulseek.NET still *initiates* downloads with direction 0
     (`SoulseekClient.cs:3575`) and still *handles* inbound direction-0 requests
     (`PeerMessageHandler.cs:285-315`);
   - Nicotine+ documents that "clients like slskd and Seeker still use this method for
     downloading, so we need to ensure we still understand such requests"
     (`pynicotine/slskmessages.py:3907-3919`);
   - the flow is still live inside slskr: hash backfill and preview streaming use
     direction 0 (`hash_backfill_runtime.rs:154`, `preview_stream_controller.rs:860`).

   The accurate claim is narrower: direction 0 is **deprecated for new download
   requests**, no longer sent by current mainstream clients, and the modern path avoids
   its extra round trip. It is not dead, and it is not ignored by the two peers that
   matter most to slskr's parity work.

4. **slskr's transfer-connection token handling is defensive but its comments are
   wrong about slskd.** Soulseek.NET sends the 4-byte transfer token after `PeerInit`
   (`PeerConnectionManager.cs:651-653`) and reads it on inbound transfer connections
   (`:543-545`). The 1.5 s token grace in `inbound_transfer.rs` is a reasonable
   compatibility measure, but the stated reason ("slskd carries it only in PeerInit")
   is not what slskd does.

5. **Queueing models differ substantially.** slskd has a global/per-group upload queue
   with `AwaitStartAsync` slot acquisition, round-robin group selection, and remote
   queue acknowledgement timeouts. slskr has a DB-backed transfer table, group
   priorities and FIFO/round-robin selection, a global `transfer_max_active` cap, and
   explicit `queued` / `peer_lookup` / `peer_negotiating` / `accepted` / `in_progress`
   states.

6. **Defaults are close for timeouts and buffers, far apart for slots and
   obfuscation.** slskd defaults to 10 upload slots, effectively unlimited downloads
   (`int.MaxValue`), and no obfuscation support. slskr defaults to 20 upload slots,
   500 download slots, `transfer_max_active = 520`, and obfuscation enabled in
   compatibility mode.

## 2. Architecture at a glance

### slskd

```
ASP.NET Core host (Program.cs)
  └── Application (connection lifecycle, event wiring, enqueue callbacks)
        ├── Transfers/Downloads/DownloadService   (EF Core-backed download records)
        ├── Transfers/Uploads/UploadService       (upload records, streams)
        ├── Transfers/Uploads/UploadQueue         (groups, slots, position)
        ├── Transfers/Uploads/UploadGovernor      (per-user rate limits)
        └── Soulseek.NET (SoulseekClient)
              ├── Server connection / login / distributed network
              ├── PeerConnectionManager (message + transfer connections)
              ├── ListenerHandler (inbound direct connections)
              └── Messaging handlers (server + peer messages)
```

- slskd owns policy: which files are shared, who may download, queue groups, retry
  strategy, destination paths, persistence.
- Soulseek.NET owns protocol: login, message framing, token allocation, connection
  races, transfer stream copying.
- slskd's download record state is `TransferStates` flags persisted through EF Core
  (`src/slskd/Transfers/Types/Transfer.cs`).

### slskr

```
slskr daemon (AppState + runtime owners)
  ├── session_runtime_owners/session_connection.rs   (login, WaitPort, distributed init)
  ├── listener_runtime.rs                            (regular/obfuscated listeners, demux)
  ├── peer_transport.rs                              (peer message + transfer dialing)
  ├── peer_message_runtime.rs                        (inbound peer dispatch, upload scheduler)
  ├── file_transfer_runtime_owners/peer_negotiation.rs
  ├── file_transfer_runtime_owners/inbound_transfer.rs
  ├── file_transfer_runtime_owners/download_connection.rs
  ├── file_transfer_runtime_owners/upload_streaming.rs
  ├── transfer_queue.rs / transfer_entry.rs          (durable transfer table)
  └── slskr-client / slskr-protocol                  (wire messages, connections)
```

- slskr owns both policy and most protocol orchestration in the daemon; the client
  crates are comparatively thin.
- Transfer state is a string status on a `TransferEntry`, persisted as a JSON
  projection and rehydrated at startup.

## 3. Connection and network setup

### 3.1 Server connection and login

**slskd**

- `Application.Connect()` builds `ProxyOptions` and `ConnectionOptions`, then patches
  the `SoulseekClient` with listen address/port and callbacks
  (`src/slskd/Application.cs:400-460`).
- `SoulseekClient.ConnectAsync` opens the server TCP connection, performs the login
  handshake, and then `SendConfigurationMessagesAsync` sends `SetListenPortCommand`
  (`SoulseekClient.cs:4701-4707`).
- slskd registers `ConnectionWatchdog` (`Program.cs:740`) and starts it after connect
  (`Application.cs:531`).
- VPN integration gates reconnect attempts: the watchdog returns early while
  `Integrations.Vpn.Enabled && !VPN.IsReady` (`ConnectionWatchdog.cs:265-275`).

**slskr**

- `session_connection.rs:80-100` opens the server TCP connection and constructs the
  initial `WaitPort` with the advertised regular port and, when enabled, an obfuscated
  port (`ROTATED_OBFUSCATION_TYPE`).
- `login_with_wait_port` performs login and port advertisement in one step.
- After login it re-sends `SetListenPort` / obfuscated port when obfuscation is enabled
  (`session_connection.rs:118-140`), then initializes the distributed network
  (`HaveNoParent`, `AcceptChildren`, `BranchLevel`, `BranchRoot`;
  `session_connection.rs:200-230`) and sends an initial ping.
- The session supervisor sends `Ping` every `ping_interval` (default 300 s;
  `session_supervision.rs:89`, `config_parts/startup.rs:179-183`).

**Difference in practice:** both advertise a listen port; slskr can advertise a second
obfuscated port, slskd cannot (see 3.3). slskd's reconnect is watchdog-driven;
slskr's is a supervision loop with a fixed delay (see 3.5).

### 3.2 Listeners and inbound classification

**slskd / Soulseek.NET**

- The listener binds `Soulseek.ListenIpAddress` (default `0.0.0.0`) on
  `Soulseek.ListenPort` (default `50300`) (`Options.cs:1762-1771`).
- `ListenerHandler` accepts connections and hands them to
  `PeerConnectionManager.AddOrUpdateMessageConnectionAsync` or the transfer
  connection path.
- Inbound direct transfer connections are read for a 4-byte remote token
  (`PeerConnectionManager.cs:543-545`); inbound indirect transfer connections are
  established by connecting out and sending `PierceFirewall` (`:580-590`).

**slskr**

- `spawn_configured_listeners` starts a regular listener and an obfuscated listener
  (`listener_runtime.rs:5-35`). When obfuscation is enabled with no dedicated port,
  the regular listener becomes a shared listener that demuxes plain, obfuscated and
  mesh TLS connections (`listener_runtime.rs:10-13`, `:445-470`).
- Each accepted connection gets a handshake permit from a bounded pool
  (`listener_runtime.rs:306-320`), then `demux_incoming` / `demux_obfuscated_incoming`
  / `demux_shared_incoming` classifies it as peer-message, file-transfer, browse,
  mesh, etc.
- Inbound handshakes are bounded by `DEFAULT_INIT_HANDSHAKE_TIMEOUT`, and failures are
  recorded with a redacted prefix for diagnostics (`listener_runtime.rs:370-430`).
- Inbound file transfers carry an optional 4-byte token frame; slskr waits up to
  1.5 s for it before sending the 8-byte offset (`inbound_transfer.rs:12`, `:45-90`).

### 3.3 Obfuscation

**slskd:** not supported. Soulseek.NET's own comment says it sends only the listen port
because "we don't support obfuscation" (`SoulseekClient.cs:4701-4703`). There is no
obfuscated listener, no obfuscated dial path, and no obfuscation option in
`Options.cs`.

**slskr:** first-class. `obfuscation_enabled` defaults to true for supported profiles,
mode is `compatibility` by default, `prefer_outbound` defaults to true, and "only" mode
is rejected because regular fallback is required (`config_parts/peer_transport.rs:77-100`,
`:700-745`). Outbound dial order is computed by `outbound_peer_dial_order`
(`peer_transport.rs:14-35`):

- `prefer` + obfuscated available → obfuscated, then regular;
- compatibility with a regular endpoint → regular only;
- no regular endpoint → obfuscated.

This is a real capability gap in slskr's favor, not a parity defect: slskr can talk to
peers that only advertise obfuscated ports, slskd cannot.

### 3.4 Peer connection establishment

**slskr**

- Message connections: `request_plain_peer_download` connects directly, sends
  `PeerInit` with connection type `P`, then negotiates. Obfuscated peers use
  `request_obfuscated_peer_download`.
- Transfers: `connect_file_transfer_preferred` dials the peer directly (regular first,
  then obfuscated per dial order) and sends `PeerInit` with type `F`
  (`peer_transport.rs:327-375`).
- If direct dialing fails, downloads fall back to an indirect connection brokered by
  the server (`ConnectToPeer`). The socket is kept open across `QueueUpload` and the
  peer's offer (`peer_transport.rs:627-704`).
- Indirect *inbound* connections are completed by sending `PierceFirewall` with the
  token (`peer_transport.rs:430-455`).
- Plain peer-message handling is intentionally short-lived: the handler reads at most
  four messages (the first blocking, later ones with a 15 s timeout) and then closes
  (`peer_message_runtime.rs:12-45`). This is the opposite of Soulseek.NET's cached,
  continuously-read message connections.

**slskd / Soulseek.NET**

- Message connections are cached per user and reused; inbound connections supersede
  cached ones (`PeerConnectionManager.cs:107-160`).
- Transfer connections are **raced**: direct and indirect are started simultaneously
  and the first success wins (`PeerConnectionManager.cs:609-660`). The loser is
  cancelled.
- After a transfer connection wins, Soulseek.NET writes `PeerInit` (direct only) and
  then the 4-byte token (`:651-653`). For indirect it sends `PierceFirewall` and then
  reads the remote token (`:580-590`).
- Downloads additionally have a "second chance" path: if the uploader does not dial
  within the transfer timeout, Soulseek.NET dials the uploader itself and logs a
  warning that the remote is "most likely Nicotine+"
  (`SoulseekClient.cs:3695-3712`).

**Behavioral difference:** Soulseek.NET races direct and indirect paths concurrently;
slskr tries direct transports first and only then asks the server for an indirect
connection. The slskr approach is simpler and avoids duplicate connections, but it
adds latency for NAT-bound peers. Soulseek.NET's "second chance" dial has no equivalent
on slskr's modern download path, which waits for the uploader to dial.

### 3.5 Timeouts, buffers, proxy, reconnect — defaults

| Setting | slskd | slskr | Source |
| --- | --- | --- | --- |
| Server address | `vps.slsknet.org` | same | `Options.cs:1707`; slskr config |
| Server port | `2271` | same | `Options.cs:1717` |
| Listen IP | `0.0.0.0` | configurable bind | `Options.cs:1762` |
| Listen port | `50300` | `50300` | `Options.cs:1771` |
| Connect timeout | 10 000 ms | 10 000 ms | `Options.cs:1882`; `config_file_parts/peer_transport.rs:201-217` |
| Inactivity timeout | 15 000 ms | 15 000 ms (legacy profile), 60 000 ms (native) | `Options.cs:1891`; `config_file_parts/peer_transport.rs:212-227` |
| Transfer timeout | 60 000 ms | 60 000 ms | `Options.cs:1900`; `config_file_parts/peer_transport.rs:227-238` |
| Read buffer | 16 384 | 16 384 | `Options.cs:1840`; slskr peer transport config |
| Write buffer | 16 384 | 16 384 | `Options.cs:1849` |
| Transfer buffer | 262 144 | 262 144 | `Options.cs:1858`; slskr config |
| Write queue | 50 | 50 | `Options.cs:1867`; slskr config |
| SOCKS5 proxy | optional, disabled | optional, disabled | `Options.cs:1914`; slskr proxy settings |
| Upload slots | 10 | 20 | `Options.cs:934`; `config_file_parts/transfer_policy.rs:420` |
| Download slots | `int.MaxValue` | 500 | `Options.cs:965`; `config_file_parts/transfer_policy.rs:456` |
| Global active cap | none (Soulseek.NET semaphores) | `transfer_max_active = 520` | `config_parts/startup.rs:420-426` |
| Download retry attempts | 3 | 3 | `Options.cs:997`; `config_file_parts/transfer_policy.rs:486` |
| Retry base delay | 5 000 ms | 5 000 ms | `Options.cs:1003`; `:488` |
| Retry max delay | 60 000 ms | 60 000 ms | `Options.cs:1009`; `:489` |
| Partial resume | `resume` | resumable | `Options.cs:1015`; `download_connection.rs:82-120` |
| Reconnect | exponential 1 s → 5 min + jitter | fixed 30 s | `ConnectionWatchdog.cs:54`, `:280`; `config_parts/startup.rs:170-178` |
| Ping interval | Soulseek.NET internal | 300 s | `session_supervision.rs:89`; `startup.rs:179-183` |

Notes:

- slskr accepts slskd's environment variable names as aliases for most network and
  transfer settings (for example `SLSKD_SLSK_*`, `SLSKD_UPLOAD_SLOTS`,
  `SLSKD_DOWNLOAD_SLOTS`), which is why the two defaults tables line up so closely.
- slskd's download slot default is effectively "no slot limit"; concurrency is bounded
  by Soulseek.NET's per-user and global semaphores and by the number of transfers the
  caller starts.
- slskr's `transfer_max_active` is a hard global cap across both directions; the
  per-direction slot counts are additional limits.

### 3.6 Reconnect behavior

**slskd**

- `ConnectionWatchdog` runs a reconnect loop. After the first failure it computes
  exponential backoff with jitter using base 1 000 ms and cap 300 000 ms
  (`ConnectionWatchdog.cs:54`, `:280-292`).
- It exits the loop on a successful connect, on stop, or on cancellation.
- VPN integration can hold reconnects until the tunnel is ready (`:265-275`).

**slskr**

- On server failure the session is marked `error`, `reconnect_pending` is set, and the
  supervisor waits `reconnect_delay` (default 30 s) before retrying
  (`session_runtime_owners/server_transport.rs:90-110`;
  `session_supervision.rs:144-170`).
- The delay is fixed, not exponential. There is no jitter.
- `Relogged` from the server forces a disconnect and a fresh session
  (`session_supervision.rs:220-245`).

**Assessment:** slskd is more resilient to a flapping server (backoff avoids hammering);
slskr is more predictable and easier to reason about. Neither is clearly "correct", but
slskr's fixed 30 s delay will reconnect 10× more often than slskd during a long outage.

## 4. Download flow

### 4.1 Admission and enqueue

**slskd**

- `DownloadService.EnqueueAsync` (`DownloadService.cs:299`) performs duplicate checks,
  creates a `Transfer` row in `Queued | Locally`, and starts a task per file
  (`:466-520`).
- It waits up to **3 minutes** for the remote "Queued" acknowledgement
  (`:424`, `:548-552`). This is a safety buffer; the comment notes that requesting
  clients usually give up after about a minute (`Application.cs:626-629`).
- Enqueue is serialized per user (`EnqueueSemaphores`) and globally
  (`EnqueueSemaphoreSyncRoot`), with a circuit breaker that rejects requests when the
  estimated wait exceeds 180 s (`Application.cs:630-650`).

**slskr**

- Downloads are rows in the durable transfer table with `direction = 0`,
  `status = "queued"`, optional `next_attempt_at`, and a stored `local_path`.
- `schedule_queued_downloads_inner` selects the oldest eligible queued download,
  respects the download slot count and `transfer_max_active`, and promotes it to
  `peer_lookup` (`peer_negotiation.rs:685-740`).
- Eligibility excludes entries without a peer or destination, entries still in
  backoff, and — outside login replay — entries whose `reason` is a remote-queue
  response (`:706-720`).

### 4.2 Negotiation

**slskd (legacy outbound, still current in slskd)**

- `SoulseekClient.DownloadAsync` opens/reuses a peer message connection and sends
  `TransferRequest(TransferDirection.Download, token, remoteFilename)`
  (`SoulseekClient.cs:3575`).
- It then waits for `TransferResponse` (`:3570-3580`). If the response is not
  `Allowed` and the message is not `"Queued"`, it throws `TransferRejectedException`
  (`:3625-3640`).
- If it is `"Queued"`, the download enters `Queued | Remotely` and waits for the
  uploader's `TransferRequest(direction = Upload)` (`:3645-3695`).
- On the offer it replies `TransferResponse(remoteToken, size)` and awaits the
  transfer connection (`:3692-3710`).

**slskr (modern, PR #214)**

- `negotiate_peer_download` (`peer_transport.rs:547-620`) is the normal download path.
  Because the uploader dials the downloader, the modern flow requires
  `transfer_allow_inbound`; slskr fails the transfer permanently when inbound transfers
  are disabled rather than retrying (`peer_negotiation.rs:389-400`).
- `queue_peer_download` sends `QueueUpload { filename }` and an optional
  `PlaceInQueueRequest` (`peer_transport.rs:748-772`).
- `await_peer_download_offer` reads until it receives `TransferRequest` with
  `direction == 1` (`:811`), or a refusal (`UploadDenied`, `UploadFailed`), or the
  offer window closes.
- On a valid offer it binds the queue entry to the peer's token, replies
  `TransferResponse::Allowed`, and waits for the uploader to dial
  (`peer_transport.rs:811-861`).
- If the window closes with no offer, the transfer is projected as `queued` with
  reason `"Queued"` and left for a later offer/new socket
  (`peer_negotiation.rs:432-450`).

**slskr also retains the legacy sender.** `negotiate_peer_transfer`
(`peer_transport.rs:460-520`) builds `TransferRequest` with
`direction: transfer.direction` and is still used by:

- hash backfill (`hash_backfill_runtime.rs:154`),
- preview streaming (`preview_stream_controller.rs:860`),
- upload start (`direction = 1`, from `project_peer_transfer_response`).

So the PR's code comment is not describing dead code. It is describing a path that the
main download scheduler no longer uses, but two other features still do.

### 4.3 Transfer connection and token/offset handshake

**slskd**

- Downloader awaits a direct or indirect connection
  (`PeerConnectionManager.AwaitTransferConnectionAsync`, `:202-260`).
- Inbound direct connections are read for a 4-byte remote token (`:543-545`).
- After the connection is established, the downloader writes the 8-byte start offset
  (`SoulseekClient.cs:3772`), then reads `Size - StartOffset` bytes.
- If no connection arrives, the downloader dials the uploader as a second chance
  (`:3695-3712`).

**slskr**

- The uploader (or the peer acting as uploader) dials slskr's listener; the listener
  demux classifies the connection as `FileTransfer` and passes the negotiated token
  when available (`listener_runtime.rs`, `peer_transport.rs:80-110`).
- `handle_inbound_file_transfer` finds the pending download by token, waits up to
  1.5 s for a 4-byte `FileTransferInit`, then sends the 8-byte offset
  (`inbound_transfer.rs:45-90`; `download_progress.rs:12-38`).
- If the peer sends no token frame, slskr keeps the negotiated token and proceeds, so
  a peer that only uses `PeerInit` does not stall the transfer.
- The modern download path has no client-initiated transfer dial after `Allowed`; it
  waits for the uploader's socket. The `download_file_transfer` dial helper is used by
  hash backfill and preview instead (`hash_backfill_runtime.rs:195`,
  `preview_stream_controller.rs:876`).

**Assessment:** slskr is deliberately more permissive at the token boundary, which is
good for interoperability. The comments describing *why* are inaccurate (see §7.4).

### 4.4 Queue position and remote-queue semantics

**slskd**

- `GetPlaceInQueueAsync` asks the peer and updates the transfer (`DownloadService.cs:717`).
- Remote-queued downloads are persisted as `Queued | Remotely`; they are not retried
  by the normal retry loop because Soulseek.NET is waiting on a `TransferRequest`
  waiter (`SoulseekClient.cs:3645-3695`).

**slskr**

- `PlaceInQueueResponse` is recorded as the transfer's `place` and logged
  (`peer_transport.rs:867-875`).
- Remote-queued entries (`status = "queued"`, `reason = "Queued"`) are skipped by the
  periodic scheduler but replayed once after login
  (`resume_queued_downloads_after_login`, `peer_negotiation.rs:681-720`). The rationale
  is documented: the peer owns the queue, but the old `QueueUpload` may be gone after a
  reconnect.
- Stalled negotiation is expired by `expire_stalled_download_negotiations`
  (`peer_negotiation.rs:570-640`): `accepted` or zero-byte `in_progress` entries older
  than `max(transfer_timeout, 30 s)` are requeued or failed.

### 4.5 Retry, backoff, partial resume

**slskd**

- `DownloadAsync` wraps the whole `Client.DownloadAsync` call in `Retry.Do`
  (`DownloadService.cs:1364`).
- Non-retryable: `OperationCanceledException`, `TransferRejectedException`,
  `DuplicateTransferException`, `TransferSizeMismatchException` (`:1405-1409`).
- Retry delay is exponential with jitter, base `download.retry.delay` and cap
  `max_delay` (`Retry.cs:116-119`).
- Partial files are stored under
  `<incomplete>/<username>/<remote path>/<filename>` and resumed with
  `FileMode.Append` and a start offset (`DownloadService.cs:1328-1400`).

**slskr**

- Negotiation failures go through `requeue_peer_download`
  (`peer_negotiation.rs:507-555`): attempts + 1, exponential delay via
  `download_retry_delay`, status back to `queued`, persisted.
- Mid-transfer failures go through `download_file_transfer_with_retry`
  (`download_connection.rs:12-80`): same transfer entry, same backoff, retries the
  whole transfer from the last persisted offset.
- Partial resume uses `prepare_incomplete_download_file` with `resume`/`overwrite`
  semantics (`download_connection.rs:82-120`).
- Retry state is persisted (`next_attempt_at`, `attempts`, `reason`), so a restart
  preserves the backoff window.

**Assessment:** the two implementations converge on the same retry policy (3 attempts,
5 s base, 60 s cap, resume partials). slskd retries the whole `DownloadAsync` call;
slskr has two retry layers (negotiation and mid-transfer) that share the same counters.

### 4.6 State model

| slskd | slskr |
| --- | --- |
| `TransferStates` flags (`Queued`, `Locally`, `Remotely`, `InProgress`, `Completed`, `Succeeded`, `Rejected`, `TimedOut`, `Errored`, `Cancelled`, `Aborted`) | status strings: `queued`, `requested`, `peer_lookup`, `peer_negotiating`, `accepted`, `indirect_pending`, `in_progress`, `succeeded`, `completed`, `cancelled`, `failed`, `rejected`, `errored` (`utils.rs:1228-1248`) |
| EF Core `Transfer` row per file | `TransferEntry` serialized to JSON projection (`transfer_entry.rs`) |
| Retry attempts stored on the row | `attempts`, `next_attempt_at` stored on the entry |

## 5. Upload flow

### 5.1 Admission and policy

**slskd**

- Incoming `QueueUpload` (Soulseek.NET calls it `QueueDownload`, code 43) and incoming
  legacy `TransferRequest(direction = 0)` both call
  `SoulseekClient.Options.EnqueueDownload`, which slskd wires to
  `Application.EnqueueDownload` (`Application.cs:460`, `:609`).
- `Application.EnqueueDownload` checks path traversal, blacklist, shares, and the
  enqueue circuit breaker, then calls `UploadService.EnqueueAsync`
  (`Application.cs:609-700`; `UploadService.cs:624`).
- Rejections are sent as `UploadDenied` (code 50) with a reason; queue acknowledgements
  are sent as `TransferResponse(token, "Queued")` for the legacy path.

**slskr**

- `handle_queue_upload_message` (`peer_message_runtime.rs:618`) checks the share index
  and `inbound_upload_policy`. Missing files get `UploadDenied` with
  `"File not shared."`.
- Policy `"Queued"` creates/updates a `direction = 1` transfer in `queued` state and
  calls `schedule_queued_uploads`.
- `handle_queued_download_request` (`peer_message_runtime.rs:677`) handles the legacy
  direction-0 request: it records a queued entry, replies
  `TransferResponse::Rejected { reason: "Queued" }`, then (when a slot is available)
  sends `TransferRequest(direction = 1)` and waits for `TransferResponse::Allowed`
  before executing the upload (`:815-860`).
- Blacklisted peers get `"File not shared."` for any transfer request
  (`peer_message_runtime.rs:167-176`).

### 5.2 Queueing and slots

**slskd**

- `UploadQueue` keeps a `ConcurrentDictionary<string, List<Upload>>` per user and a set
  of groups (`UploadQueue.cs:137-145`).
- `Enqueue` adds the transfer to the user's list and updates the group
  (`UploadQueue.cs:273`).
- `AwaitStartAsync` blocks until the transfer is selected by the group scheduler;
  `UploadService` passes it as `slotAwaiter` to `Client.UploadAsync`
  (`UploadService.cs:442-449`).
- `UploadQueue` supports group priorities and `roundrobin` / `fifo` strategies
  (`Options.cs:1150-1155`).
- `ForecastPosition` / `EstimatePosition` provide queue positions
  (`UploadQueue.cs:320`, `:425`).
- Per-user upload concurrency is enforced by Soulseek.NET
  (`MaximumConcurrentUploadsPerUser`, `SoulseekClient.cs:4844`) and by
  `UploadGovernor` for rate limits.

**slskr**

- `next_queued_upload_id` (`peer_message_runtime.rs:380-443`) selects an upload by
  group priority, then FIFO or round-robin, subject to:
  - global `transfer_max_active`;
  - global `upload.slots`;
  - per-group `slots`.
- `schedule_queued_uploads` promotes the selected entry to `peer_lookup`, asks the
  session for the peer endpoint, and later starts the transfer.
- Queue positions are computed in `upload_queue_position_from`
  (`peer_message_runtime.rs:488-552`) with the same group/strategy rules.
- `upload_queue_forecast_from` returns `(slots, position)` for the UI/API
  (`:554-600`).

**Assessment:** both are group-aware and support FIFO/round-robin. slskd's queue is
in-memory and rebuilt from the database on startup; slskr's queue is the transfer table
itself, so queue order survives restarts without a rebuild step.

### 5.3 Start handshake and transfer

**slskd (as uploader)**

- `UploadService.UploadAsync` acquires the queue slot, then calls
  `Client.UploadAsync` (`UploadService.cs:442-470`).
- Soulseek.NET sends `TransferRequest(TransferDirection.Upload, token, filename, size)`
  on the peer message connection (`SoulseekClient.cs:4893`) and waits for
  `TransferResponse` (`:4889-4905`).
- On `Allowed` it opens a transfer connection (`GetTransferConnectionAsync`,
  `:4906-4912`), writes `PeerInit` (direct) and the 4-byte token (`:651-653`), then
  reads the 8-byte offset (`:4938`) and streams the file.

**slskr (as uploader)**

- `execute_accepted_file_transfer` calls `upload_file_transfer`
  (`peer_negotiation.rs:88-100`), which dials the downloader with
  `connect_file_transfer_preferred`.
- `upload_file_transfer_with_connection` sends the 4-byte token when `send_token` is
  true (`upload_streaming.rs:55-66`), reads the 8-byte offset (`:68-75`), seeks, and
  streams (`:82+`).
- For the legacy direction-0 path, the start request is sent inline and the response is
  awaited with `timeout_inactivity` (`peer_message_runtime.rs:815-860`).

**Difference:** slskd always requests the transfer over the existing peer message
connection and lets Soulseek.NET manage the transfer connection race. slskr re-dials the
peer for the transfer connection (direct first, obfuscated second) and relies on its own
listener for inbound transfers. Both send the token, both read the offset.

### 5.4 Completion and failure reporting

**slskd / Soulseek.NET**

- On failure the uploader sends `UploadDenied` (cancelled) or `UploadFailed` (other)
  over a message connection (`SoulseekClient.cs:5130-5160`).
- The downloader maps `UploadDenied` to `TransferRejectedException` and `UploadFailed`
  to `TransferReportedFailedException` (`PeerMessageHandler.cs:319-346`).

**slskr**

- `record_expected_upload_failure` records expected failures without treating them as
  daemon errors (`peer_negotiation.rs:100-110`).
- Cancelled/failed uploads update the transfer status and schedule the next queued
  upload (`schedule_queued_uploads` after completion).
- The downloader side handles `UploadDenied`/`UploadFailed` as explicit rejections in
  `await_peer_download_offer` (`peer_transport.rs:845-860`).

## 6. Configuration surface

slskr mirrors a large part of slskd's YAML/env surface, including the `SLSKD_*`
prefixes, and adds its own `SLSKR_*` and controller-profile layers. The practical
consequences:

- A slskd config can be migrated to slskr for the network/transfer subset with few
  changes (address, port, listen port, timeouts, buffers, proxy, slots, retry).
- slskr-only settings: obfuscation mode/ports, `transfer_max_active`,
  `transfer_allow_inbound`, `transfer_allow_outbound`, mesh/DHT, relay, controller
  profiles.
- slskd-only settings: VPN port forwarding and polling, relay agent/file streaming,
  integrations (FTP, Pushbullet, scripts, webhooks), HTTP API/auth.

## 7. PR #214: the "legacy outbound" claim

### 7.1 Exact wording

Commit `2bb5eae9` ("feat(transfers): negotiate downloads with modern QueueUpload")
says:

> Current peers answer a download request with `TransferRequest { direction: 1 }`
> and then dial our listener; the legacy outbound `TransferRequest { direction: 0 }`
> handshake is ignored. Send `QueueUpload` over the peer-message socket, keep the
> server-brokered connection for the peer's offer when a direct dial is not possible,
> and project accepted/queued/rejected outcomes onto the transfer entry.

The surviving code comment is at
`crates/slskr/src/file_transfer_runtime_owners/peer_negotiation.rs:376-383`:

> Queue a download with a peer using the current Soulseek flow.
>
> Uploaders no longer answer `TransferRequest { direction: 0 }`; the downloader sends
> `QueueUpload`, and the uploader eventually answers with `TransferRequest
> { direction: 1 }` carrying its own token. We allow that offer and wait for the
> uploader to dial us. Dialing the peer ourselves only ever produces a silent stall.

### 7.2 What the protocol says

Nicotine+ is the most explicit reference (`pynicotine/slskmessages.py:3907-3919`):

> This message is sent by a peer once they are ready to start uploading a file. A
> `TransferResponse` message is expected from the recipient, either allowing or
> rejecting the upload attempt.
>
> This message was formerly used to send a download request (direction 0) as well, but
> Nicotine+ >= 3.0.3, Museek+ and the official clients use the `QueueUpload` message
> for this purpose today. **Clients like slskd and Seeker still use this method for
> downloading, so we need to ensure we still understand such requests.**

Nicotine+ also documents `QueueUpload` as "the modern replacement to a
`TransferRequest` with direction 0" (`pynicotine/uploads.py:918-925`) and still
implements the legacy handler (`pynicotine/downloads.py:1101-1163`).

### 7.3 Evidence matrix

| Implementation | Initiates downloads with | Accepts direction-0 requests | Accepts QueueUpload | Sends direction-1 offer |
| --- | --- | --- | --- | --- |
| slskd / Soulseek.NET | `TransferRequest(Download)` (`SoulseekClient.cs:3575`) | Yes (`PeerMessageHandler.cs:285-315`) | Yes (`PeerMessageHandler.cs:269-281`) | Yes (`SoulseekClient.cs:4893`) |
| Nicotine+ | `QueueUpload` (`downloads.py:383`) | Yes (`downloads.py:1101-1163`) | Yes (`uploads.py:918`) | Yes (upload start) |
| Seeker | Legacy (per Nicotine+ comment) | Not stated (uploaders must answer it for Seeker to work) | Unknown | Unknown |
| slskr (PR branch) | `QueueUpload` (`peer_transport.rs:759`) | Yes (`peer_message_runtime.rs:677`) | Yes (`peer_message_runtime.rs:618`) | Yes (`peer_message_runtime.rs:825`) |
| slskr (hash backfill/preview) | `TransferRequest(Download)` (`peer_transport.rs:473`) | n/a | n/a | n/a |

### 7.4 What is true and what is not

**True:**

- `QueueUpload` is the modern/preferred request message.
- Current mainstream clients no longer *initiate* direction-0 requests.
- The modern path is what a well-behaved uploader expects, and it avoids the extra
  request/response round trip that direction 0 requires.
- Some peers may ignore direction 0 in practice; the protocol does not guarantee it.

**Not true:**

- "Uploaders no longer answer direction 0." slskd answers it; Nicotine+ answers it;
  Seeker is documented as using it.
- "That legacy flow is silently ignored by current peers." It is answered by the two
  implementations slskr most needs to interoperate with.
- "Dialing the peer ourselves only ever produces a silent stall." slskr's own hash
  backfill and preview paths dial after a direction-0 negotiation
  (`hash_backfill_runtime.rs:195`, `preview_stream_controller.rs:876`), and
  Soulseek.NET's download path dials the peer as a "second chance" when the uploader
  does not (`SoulseekClient.cs:3695-3712`). Dialing is a valid recovery path, not a
  guaranteed stall.

**Why the confusion is understandable:** the *uploader-side* direction-1 message and
the *downloader-side* direction-0 message share code 40 and differ only by the
direction field. It is easy to read "the uploader sends direction 1" as "direction 0 is
obsolete". But the two directions describe different halves of the handshake, not
different protocol versions.

### 7.5 Recommended wording

Replace the comment at `peer_negotiation.rs:376-383` with something like:

```rust
/// Queue a download with a peer using the current Soulseek flow.
///
/// `QueueUpload` is what current clients send: Nicotine+ >= 3.0.3, Museek+ and the
/// official clients use it, and uploaders answer with `TransferRequest
/// { direction: 1 }` carrying their own token. We allow that offer and wait for the
/// uploader to dial us.
///
/// The older `TransferRequest { direction: 0 }` request is deprecated for new
/// downloads but is still understood by slskd, Seeker and Nicotine+, so
/// `negotiate_peer_transfer` keeps it for hash backfill and preview streaming.
/// Prefer `QueueUpload` for user-facing downloads: it avoids the extra round trip and
/// matches what current peers expect.
```

And adjust the commit-message wording in the PR description from "silently ignored by
current peers" to "deprecated; still accepted by slskd, Seeker and Nicotine+, but no
longer sent by current clients".

### 7.6 The second inaccurate comment

`inbound_transfer.rs:44-49` says:

> Every reference client that announces the transfer token on the file-transfer socket
> (Nicotine+, SoulseekQt) writes it in the same burst as `PeerInit`; slskd/Soulseek.NET
> carries it only in `PeerInit`.

Soulseek.NET actually writes `PeerInit` **and then** the 4-byte token on outbound
transfer connections (`PeerConnectionManager.cs:651-653`), and reads the 4-byte token on
inbound transfer connections (`:543-545`). The 1.5 s grace is still a good defensive
measure for peers that omit the frame, but the rationale should be "the frame is
optional in practice", not "slskd puts it only in PeerInit".

The same applies to `download_progress.rs:22-24` ("A peer that carried its token in
`PeerInit` sends no `FileTransferInit`").

## 8. Divergences worth tracking

| Area | slskd | slskr | Risk / note |
| --- | --- | --- | --- |
| Download request | `TransferRequest(0)` | `QueueUpload` | slskr is more modern; both accept each other's requests |
| Transfer connection race | direct + indirect simultaneously | direct first, then indirect | slskr adds latency for NAT peers; slskd may open duplicate connections |
| Token frame | always sent/read | optional, 1.5 s grace | good interop; comments need correction |
| Obfuscation | unsupported | supported (compatibility/prefer) | slskr can reach peers slskd cannot |
| Download slots | unlimited by default | 500 + global 520 | slskr bounds resource use more aggressively |
| Upload slots | 10 | 20 | cosmetic default difference |
| Reconnect | exponential 1 s–5 min + jitter | fixed 30 s | slskr reconnects more often during outages |
| Remote queue replay | waits on Soulseek.NET waiter | replays once after login | slskr recovers from lost QueueUpload messages |
| Retry | whole `DownloadAsync` call | negotiation + mid-transfer layers | same policy, different granularity |
| Persistence | EF Core rows | JSON projection + SQLite | different failure modes on restart |

## 9. Recommendations

1. **Fix the PR #214 wording before merge.** The QueueUpload change is correct; the
   justification is not. Use the wording in §7.5. This matters because the claim is
   checkable and wrong, and because slskr still uses the legacy path internally.

2. **Correct the token-handshake comments** in `inbound_transfer.rs` and
   `download_progress.rs` (§7.6). Keep the 1.5 s grace; change the explanation.

3. **Consider a configurable reconnect backoff for slskr.** The fixed 30 s delay is
   simple, but a flapping server will see 120 attempts/hour. slskd's 1 s → 5 min
   exponential with jitter is a better default. This is a behavior change and should be
   opt-in or bounded.

4. **Document the download-slot semantics.** slskr's 500/520 defaults are much lower
   than slskd's unlimited default. That is defensible, but it should be in the
   configuration docs so users migrating from slskd are not surprised.

5. **Add an interop test for the legacy direction-0 path.** Since slskr still uses it
   for hash backfill and preview, and since slskd/Nicotine+ still answer it, a
   regression test that exercises direction 0 against a stub peer would protect both
   the legacy and modern paths.

6. **Keep the modern path as the default.** No change needed there; the evidence
   supports QueueUpload-first for user downloads.

## 10. Appendix: source index

### slskr

| Topic | File:line |
| --- | --- |
| Modern download negotiation | `crates/slskr/src/peer_transport.rs:547-620` |
| "Silently ignored" comment | `crates/slskr/src/file_transfer_runtime_owners/peer_negotiation.rs:376-383` |
| Legacy sender | `crates/slskr/src/peer_transport.rs:460-520` |
| QueueUpload send | `crates/slskr/src/peer_transport.rs:748-772` |
| Offer handling | `crates/slskr/src/peer_transport.rs:777-861` |
| Indirect download | `crates/slskr/src/peer_transport.rs:627-704` |
| Transfer dial | `crates/slskr/src/peer_transport.rs:327-410` |
| Inbound token grace | `crates/slskr/src/file_transfer_runtime_owners/inbound_transfer.rs:12`, `:45-90` |
| Offset write | `crates/slskr/src/file_transfer_runtime_owners/download_progress.rs:30-38` |
| Mid-transfer retry | `crates/slskr/src/file_transfer_runtime_owners/download_connection.rs:12-80` |
| Partial resume | `crates/slskr/src/file_transfer_runtime_owners/download_connection.rs:82-120` |
| QueueUpload admission | `crates/slskr/src/peer_message_runtime.rs:618-676` |
| Legacy admission | `crates/slskr/src/peer_message_runtime.rs:677-860` |
| Upload scheduler | `crates/slskr/src/peer_message_runtime.rs:445-480` |
| Upload slot selection | `crates/slskr/src/peer_message_runtime.rs:380-443` |
| Upload start | `crates/slskr/src/file_transfer_runtime_owners/upload_streaming.rs:12-90` |
| Status model | `crates/slskr/src/utils.rs:1228-1248` |
| Retry requeue | `crates/slskr/src/file_transfer_runtime_owners/peer_negotiation.rs:507-555` |
| Stall expiry | `crates/slskr/src/file_transfer_runtime_owners/peer_negotiation.rs:570-640` |
| Login replay | `crates/slskr/src/file_transfer_runtime_owners/peer_negotiation.rs:681-720` |
| Login / port advertisement | `crates/slskr/src/session_runtime_owners/session_connection.rs:80-145` |
| Reconnect delay | `crates/slskr/src/config_parts/startup.rs:170-178` |
| Ping interval | `crates/slskr/src/config_parts/startup.rs:179-183` |
| Timeouts / buffers | `crates/slskr/src/config_file_parts/peer_transport.rs:195-245` |
| Obfuscation modes | `crates/slskr/src/config_parts/peer_transport.rs:77-100`, `:700-745` |
| Listener demux | `crates/slskr/src/listener_runtime.rs:430-500` |

### slskd

| Topic | File:line |
| --- | --- |
| Client construction | `src/slskd/Program.cs:725-735` |
| Connection options | `src/slskd/Application.cs:400-460` |
| Enqueue callback | `src/slskd/Application.cs:460`, `:609` |
| Download enqueue | `src/slskd/Transfers/Downloads/DownloadService.cs:299-520` |
| 3-minute ack limit | `src/slskd/Transfers/Downloads/DownloadService.cs:424` |
| Download start | `src/slskd/Transfers/Downloads/DownloadService.cs:1170-1290` |
| Retry wrapper | `src/slskd/Transfers/Downloads/DownloadService.cs:1364-1450` |
| Upload start | `src/slskd/Transfers/Uploads/UploadService.cs:272-470` |
| Upload enqueue | `src/slskd/Transfers/Uploads/UploadService.cs:624` |
| Upload queue | `src/slskd/Transfers/Uploads/UploadQueue.cs:273-430` |
| Queue slot await | `src/slskd/Transfers/Uploads/UploadService.cs:442-449` |
| Watchdog backoff | `src/slskd/Core/ConnectionWatchdog.cs:54`, `:280-292` |
| Network defaults | `src/slskd/Core/Options.cs:1707-1917` |
| Slot / retry defaults | `src/slskd/Core/Options.cs:934-1015` |
| Group strategy | `src/slskd/Core/Options.cs:1150-1155` |

### Soulseek.NET

| Topic | File:line |
| --- | --- |
| Legacy download request | `src/SoulseekClient.cs:3575` |
| Queued + offer wait | `src/SoulseekClient.cs:3645-3712` |
| Offset write | `src/SoulseekClient.cs:3772` |
| Upload request | `src/SoulseekClient.cs:4893-4905` |
| Offset read | `src/SoulseekClient.cs:4938` |
| Upload failure messages | `src/SoulseekClient.cs:5130-5160` |
| Peer message dispatch | `src/Messaging/Handlers/PeerMessageHandler.cs:269-315` |
| Inbound transfer token read | `src/Network/PeerConnectionManager.cs:543-545` |
| Transfer connection race | `src/Network/PeerConnectionManager.cs:609-660` |
| Outbound token write | `src/Network/PeerConnectionManager.cs:651-653` |
| Obfuscation unsupported | `src/SoulseekClient.cs:4701-4703` |
| SetListenPort | `src/SoulseekClient.cs:4705-4707` |

### Nicotine+

| Topic | File:line |
| --- | --- |
| TransferRequest docs | `pynicotine/slskmessages.py:3907-3919` |
| FileTransferInit | `pynicotine/slskmessages.py:4197-4213` |
| QueueUpload docs | `pynicotine/uploads.py:918-925` |
| Legacy request handling | `pynicotine/downloads.py:1101-1163` |
| Download initiation | `pynicotine/downloads.py:383` |
