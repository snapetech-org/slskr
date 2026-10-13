# Runtime benchmarks

Status: diagnostic-only. These commands are explicit, operator-run
measurements; the repository does not claim a nightly baseline or a CI timing
threshold until a retained workload artifact is produced for the target
environment.

The maintained HTTP benchmark is [`scripts/benchmark-http.py`](../scripts/benchmark-http.py).
It talks to a real running daemon and emits JSON with status counts, errors,
throughput, and bounded latency samples.

The dated [slskR/slskd idle-container report](artifacts/20261012-idle-container-slskr-slskd.md)
records three 10-minute CPU/RSS trials per profile: the matched, disconnected
slskd/slskR pair and slskR with DHT enabled on Docker bridge networking. The
maintained [`compare-idle-containers.py`](compare-idle-containers.py) runner
writes the [matched raw JSON](artifacts/20261012-idle-container-repeats.json)
and [DHT-on raw JSON](artifacts/20261012-idle-container-slskr-dht.json). Run
`--profiles slskd slskr slskr-dht` to collect the full matrix. The DHT-on profile
must use bridge networking and is documented separately from the no-network
matched pair. These are diagnostic measurements, not regression thresholds;
they do not exercise a Soulseek login, shares, transfers, or user-facing HTTP
workloads.
The runner generates fresh random local status credentials for each trial,
passes them through the container environment and request headers, and does
not save them in measurement artifacts; slskd's trial key is read-only.
Before recording image metadata, it pulls each selected pinned image digest if
the local daemon does not already have it.

Run all three profiles with the same repetition and window settings:

```bash
python3 benchmarks/compare-idle-containers.py \
  --profiles slskd slskr slskr-dht \
  --repeats 3 \
  --warmup-seconds 180 \
  --duration-seconds 600 \
  --sample-interval-seconds 60 \
  --output target/perf/idle-container-matrix.json
```

This takes about 117 minutes at those settings. The DHT profile needs outbound
network access; its authenticated status checks use an ephemeral host port
bound to loopback and occur outside the CPU windows.

## Live Soulseek session matrix

The live runner uses the same three profiles with a dedicated test account:
`slskd`, slskR with DHT disabled, and slskR with DHT enabled. All profiles use
Docker bridge networking and connect sequentially to the same Soulseek
endpoint. The runner verifies the authenticated session immediately before
and after each measurement window; slskR's DHT status is also checked at those
boundaries. These checks are outside the CPU window. The measurements cover
connected idle only: no shares, share scans, searches, transfers, or UI/API
workloads are configured or exercised. DHT-on is an additional profile, not a
claim that every slskR feature is enabled or under load.

Provide a dedicated test account through `SLSKR_LIVE_BENCH_USERNAME` and
`SLSKR_LIVE_BENCH_PASSWORD` in the runner's environment. The runner passes
those values to containers without writing them to its JSON artifact or
command-line arguments.

```bash
python3 benchmarks/compare-idle-containers.py \
  --profiles slskd slskr slskr-dht \
  --live-session \
  --repeats 3 \
  --warmup-seconds 180 \
  --duration-seconds 600 \
  --sample-interval-seconds 60 \
  --output target/perf/live-soulseek-idle-matrix.json
```

This takes about 117 minutes, plus login time. CPU is the cgroup v2
`cpu.stat` usage delta; the percentage is normalized to one logical CPU. The
artifact also retains process RSS and cgroup memory samples, session/DHT
boundary status, host CPU busy percentage, and load average for every trial.
Each raw artifact records every started trial attempt, separately from
completed measurements. Failed login, API, or cgroup reads retain the profile,
attempt number, UTC start and finish times, and failure reason before the runner
stops, so retries and denominator changes can be audited.
Process RSS is reported only when every PID returned by Docker has a readable
`/proc/<pid>/status` entry with a `VmRSS` row; otherwise the RSS total is null
and `rss_complete` is false. PSS completeness is recorded independently.
Keep host-specific results separate and report host load: CPU-time samples
from different machines or materially different background load are not a
controlled head-to-head comparison. The retained [2026-10-12 live matrix
report](artifacts/20261012-live-soulseek-idle.md) links the raw trials and
documents the observed host conditions and exclusions.

Example:

```bash
python3 scripts/benchmark-http.py \
  --base-url http://127.0.0.1:5030 \
  --profile native \
  --persistence disabled \
  --warmup 5 \
  --duration 30 \
  --concurrency 8 \
  --output target/perf/native-disabled.json
```

Add an authorization header when the daemon requires it:

```bash
python3 scripts/benchmark-http.py \
  --base-url http://127.0.0.1:5030 \
  --bearer-token "$SLSKR_API_TOKEN" \
  --endpoint 'GET /api/stats' \
  --endpoint 'GET /api/transfers/downloads'
```

The benchmark is intentionally limited to safe read methods. Mutation and
SignalR workloads belong in explicit scenario runners so their side effects
and event ordering remain visible rather than being hidden in a generic load
test.

Compare like-for-like live artifacts with explicit regression policy:

```bash
python3 scripts/compare-benchmark.py \
  target/perf/native-disabled-before.json \
  target/perf/native-disabled-after.json \
  --max-latency-regression-percent 10 \
  --max-throughput-regression-percent 10 \
  --output target/perf/native-disabled-comparison.json
```

The comparison rejects mismatched profiles, persistence labels, endpoint
workloads, status policies, concurrency, and timing settings. It reports
latency, throughput, and failure-rate checks for the aggregate and every
endpoint case; it does not silently treat missing measurements as a pass.

For persistence work, profile explicit read-only statements with
[`scripts/profile-sqlite.py`](../scripts/profile-sqlite.py). Its artifact pairs
the real SQLite query plan with bounded timing samples and row-count ranges,
so index or query changes can be evaluated against the same database shape.

The old standalone `benchmarks/benchmark.rs` simulated requests and was not a
valid performance measurement; it has been removed.

The file-transfer payload harness compares the former per-chunk `flush` path
with the current writer over real loopback TCP sockets. It validates received
plain and obfuscated payloads and reports bounded throughput samples. Tokio's
`TcpStream::flush` is a no-op, so results measure only local method-call and
scheduling effects; they do not establish throughput changes with remote peers.

```bash
cargo bench --locked -p slskr-client --bench file_transfer_payload -- \
  --mib 64 \
  --chunk-bytes 81920 \
  --trials 5 \
  --output benchmarks/artifacts/file-transfer-loopback.json
```

Keep a copy of the complete JSON output with any before/after report. Record
the toolchain and host conditions alongside it; compare only artifacts from
the same machine and workload. Cargo runs this harness from the
`crates/slskr-client` package directory, so relative `--output` paths resolve
there.

For the RF-021 SQLite indexes, the synthetic cardinality harness creates
production-shaped tables, compares the existing indexes with the retained
transfer/webhook composites, and profiles first and deep pages. Its generated
rows are diagnostic; production database cardinality and the daemon's bundled
SQLite version are separate evidence.

```bash
python3 benchmarks/benchmark-sqlite-cardinality.py \
  --output benchmarks/artifacts/sqlite-cardinality.json
```

The RF-046 search-response diagnostic compares the current fingerprint bucket
with the former linear equality scan using 900 seeded responses, 11 files per
response, and 900 duplicates of the final seeded response. The benchmark uses
the production `SearchResults` acceptance path for the current implementation
and a direct `Vec::contains` reference for the former comparison. It is
diagnostic only and sets no CI timing threshold.

```bash
cargo bench --locked -p slskr-client --bench search_response_dedup -- \
  --output benchmarks/artifacts/search-response-dedup.json
```

The RF-038 share-cache diagnostic compares the production writer with its
previous `replace`/`format!`/`Vec<String>` serializer. It generates 50,000 file
entries with a bounded mix of tabs, newlines, and backslashes, verifies that
both implementations produce identical bytes, and records allocation calls,
requested bytes, and elapsed time. It requires no daemon, network, or database
and is not a CI threshold.

```bash
cargo run --locked -p slskr --features rf-benchmarks \
  --example share_cache_allocations -- \
  --output benchmarks/artifacts/share-cache-allocations.json
```

The RF-045 diagnostic replays a 10,000-result search projection in 50 batches
through both the current delta-append writer and the former full-projection
rewrite. It also kills a child process after committed writes and checks the
projection after reopening the database. The workload uses temporary in-memory
or local SQLite databases and opens no network listener.

```bash
cargo run --locked -p slskr --features rf-benchmarks \
  --example search_result_delta -- \
  --output benchmarks/artifacts/search-result-delta.json
```
