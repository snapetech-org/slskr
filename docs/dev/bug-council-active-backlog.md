# Bug Council Active Backlog

This backlog is the durable handoff for `scripts/run-council-scan.sh`.
A green all-phases council run is not proof that no bugs exist; this file
records the active discovery piles that still need review, splitting, or
burn-down.

Scan date: 2026-10-16
Source digest: e80e1136dc42b363e01704ddb6fa2b53721235a26153aa2710fdf7f49b4a6d1c

Every council scan candidate class must have a row below with the current
candidate count. `scripts/check-council-active-backlog.sh` fails when a class is
missing, left `Untriaged`, or has a stale count.

Status meanings:

- `Open` - broad queue still needs classification or narrower subgroup probes.
- `Guarded` - current candidates are classified and protected by remediation checks.
- `Accepted` - confirmed bug class exists and is being fixed.
- `Existing guard` - candidates are covered by existing behavior and gates.
- `False positive` - scanner shape is not a bug for the listed rationale.
- `Out of scope` - candidate belongs outside this council.

| Section | Candidate count | Status | Current classification | Next action |
| --- | ---: | --- | --- | --- |
| `Constructor/mutable collection candidates` | 10 | Guarded | Current constructor candidates are classified in `docs/dev/council-scan-inventory.md`; the accepted Python mutable-input bug is fixed and Rust constructors own or clone their inputs. | Reopen only when fresh candidates are not covered by BUG-032 or the existing ownership evidence. |
| `Protocol count/length candidates` | 164 | Guarded | Current count/length candidates are classified; accepted raw-frame, transfer-chunk, and protocol loop-bound bugs are fixed, with taint/adversarial gates covering high-risk parser paths. | Reopen only when a fresh wire-derived allocation/read/loop flow is not covered by BUG-033, BUG-035, BUG-040, or existing bounded-count evidence. |
| `Protocol scalar emission candidates` | 309 | Guarded | The widened production-module scalar scan was reviewed by narrowing and signed-conversion class. Four wrapping paths in share metadata, distributed state, wishlist scheduler state, and user timestamps were fixed; remaining length/code emissions are bounded, checked, or inventory-tested. | Reopen only when a fresh protocol-visible narrowing path lacks a checked conversion or discriminant inventory evidence. |
| `Resolver/raw stream candidates` | 1093 | Guarded | Current candidates are classified. The server-brokered peer-message flow validates the `PierceFirewall` token against pending work before sending and retains direct-listener and endpoint policies; real-socket regressions verify direct delivery and brokered fallback. Counts are scanner matches, not confirmed bugs. Raw-frame/connect-timeout regressions and daemon/SDK timeout, resolver, and frame-size checks remain active. | Reopen a finding when a production socket/resolver/read path lacks timeout, address policy, or size-bound evidence. |
| `Task/cancellation/lifecycle candidates` | 1599 | Guarded | Current lifecycle candidates are classified; accepted TypeScript timer/default bugs and the legacy multisource shutdown gap are fixed. Daemon/WebSocket/webhook/script/port-forward ownership is covered by bounded channels, timeouts, and shutdown tests; HTTP handlers share a 256-task cap and service work uses bounded admission or managed ownership. New share progress uses one worker plus a 100 ms state publisher; indirect peer-message requests have one-shot completion, timeout cleanup, and server failure cleanup, and successful direct sends avoid duplicate broker requests. The new bounded log-check polling in the share-scan regression is test-only. | Reopen only when a fresh spawn/timeout/channel path lacks shutdown, bounded queue, or cleanup evidence. |
| `Example Web API candidates` | 348 | Guarded | Current web/API examples are classified; the 31 fresh matches are language and regional-format setting paths/tests, including non-secret UI values in browser storage. API tokens remain session-only under the browser token persistence gate; safe opener, CORS, and docs freshness checks remain active. | Reopen when a fresh example bypasses the SDK auth helpers, hard-codes secrets, or contradicts deployment posture. |
| `Async void boundaries` | 0 | Existing guard | The current scan has no async-void candidates in the scoped source trees; async operations either return their result or are explicitly owned by a task boundary. | Reopen when a fresh candidate appears. |
| `Silent catch or lossy exception boundaries` | 0 | Existing guard | The current scan has no unclassified silent-catch candidates; optional compatibility reads distinguish 404 fallbacks from outages and auth/network failures. | Reopen when a fresh candidate appears. |
| `Callback/event invocation boundaries` | 0 | Existing guard | The current scan has no callback/event candidates requiring classification; event and callback paths are covered by the existing lifecycle and bounded-queue guards. | Reopen when a fresh candidate appears. |
| `Remote/user text in diagnostics or HTTP errors` | 0 | Existing guard | The current scan has no candidates in this class; remote text is rendered through React text nodes and error responses are bounded by existing route handling. | Reopen when a fresh candidate appears. |
| `Public mutable ownership surfaces` | 0 | Existing guard | The current scan has no public mutable ownership candidates requiring classification; SDK and browser helpers copy or normalize mutable payloads at their boundaries. | Reopen when a fresh candidate appears. |
