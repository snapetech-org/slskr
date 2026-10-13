# Idle container comparison: slskR and slskd (2026-10-12)

## Summary

**Status:** repeated, diagnostic release-image benchmark. It compares these two
pinned images under the disconnected conditions below. It is not a CI threshold,
a comparison of every feature, or a prediction for a NAS with an active
Soulseek session, configured shares, transfers, or UI/API clients.

**Confidence:** high that the reported CPU values accurately summarize the
recorded cgroup counters; moderate that slskR used less CPU than slskd in this
specific disconnected-idle setup; low that the result predicts another host or
a connected workload. Three trials per image on one busy host are useful
replication, but they are not a broad benchmark campaign.

The primary result is the **median of the three repetition-matched CPU-time
ratios**: slskd used 15.98 times the CPU time of slskR in this test. The
individual paired ratios were 14.37x, 15.98x, and 20.75x. This does not explain
the reported 28% reading: the benchmark intentionally disconnected both
daemons and does not reproduce the reporter's NAS, settings, or monitor.

A third profile adds slskR with DHT enabled and connected to the public DHT,
while its Soulseek account remains disconnected. That profile's median was
0.075594% of one logical CPU. It uses bridge networking, unlike the two
network-disabled matched profiles, so it is shown as an additional workload
column and not as a like-for-like CPU ratio. “DHT-on idle” describes this
measured profile; it does not mean every feature was exercised under load.

## Repeated result

Each fresh container received a 180-second warm-up followed by a 600-second
measurement window. CPU was read from the container's cgroup v2 `cpu.stat`
counter. Percentages below are on a **one-logical-CPU scale**: 100% means one
logical CPU occupied for the full window, not 100% of the entire host.

| Image | Median CPU time per 600 s | Median one-core CPU | Range across 3 trials | Summed process RSS sampled during windows |
| --- | ---: | ---: | ---: | ---: |
| slskR v0.2.56 | 0.173476 s | 0.028901% | 0.024271–0.034123% | 20.8–24.7 MiB |
| slskd 0.26.1 | 2.943921 s | 0.490465% | 0.461732–0.503670% | 130.1–219.0 MiB |

The paired CPU-time ratios are calculated within each repetition number, then
the median of those three ratios is reported. This is **not** the ratio of the
two medians (which is about 16.97x). The paired values are:

| Repetition | slskR CPU time | slskd CPU time | slskd / slskR |
| --- | ---: | ---: | ---: |
| 1 | 0.204813 s | 2.943921 s | 14.37x |
| 2 | 0.173476 s | 2.771776 s | 15.98x |
| 3 | 0.145679 s | 3.023154 s | 20.75x |

| Repetition | slskR one-core CPU | slskd one-core CPU | Recorded host CPU busy (legacy) |
| --- | ---: | ---: | ---: |
| 1 | 0.034123% | 0.490465% | slskR 21.90%; slskd 16.26% |
| 2 | 0.028901% | 0.461732% | slskR 14.47%; slskd 14.35% |
| 3 | 0.024271% | 0.503670% | slskR 15.63%; slskd 16.94% |

Legacy host-busy figures were collected before the runner excluded
guest and `guest_nice` ticks from `/proc/stat`. Linux already includes those
ticks in user and nice, so the figures may be overstated. The raw artifacts do
not retain the individual host tick deltas needed to recompute them; current
reruns use the corrected accounting.

The CPU ranges do not overlap in these six trials. The host was nevertheless
not idle: unrelated workloads were running, and recorded legacy aggregate
host CPU busy ranged from 14.3% to 21.9%. The order alternated to reduce
simple time-order bias:
slskR then slskd for repetition 1, slskd then slskR for repetition 2, and
slskR then slskd for repetition 3. The comparison is sequential, so the two
containers did not compete with each other for CPU.

Both containers had `cpu.max` set to `max 100000`; `nr_throttled` did not
increase in any trial. The runner read cgroup counters from the host and did
not use `docker exec` or a profiler inside the measured container.

## Memory result and limits

The RSS numbers are the minimum and maximum of the one-minute samples across
all three trials. RSS is the sum of `VmRSS` for processes visible in each
container (`slskR`: one process; `slskd`: two). The sampled RSS ranges did not
overlap, but slskd varied substantially: repetition 2 ranged from 130.1 to
215.8 MiB, while repetitions 1 and 3 were near 202–219 MiB. The run does not
identify why repetition 2 changed, so no cause is assigned.

No single steady-state memory multiplier is claimed. Process RSS can count
shared pages more than once and does not include all memory charged to the
container. The runner also records cgroup `memory.current` and selected
`memory.stat` fields, but those include file cache and shared memory and should
not be treated as process RAM or compared directly with a dashboard's
working-set figure. PSS was attempted but could not be read for the root-owned
container processes with this host user's permissions; the raw artifact marks
PSS as unavailable.

## Expanded profile matrix

The matched pair uses the same disconnected, no-share, no-request scenario.
The third column adds the default native slskR feature profile with DHT
enabled. That profile needs network access to reach DHT peers; slskd and the
matched slskR column remain on `--network none`.

| Measurement | slskd 0.26.1, matched idle | slskR v0.2.56, matched idle | slskR v0.2.56, DHT-on idle |
| --- | ---: | ---: | ---: |
| Median CPU time per 600 s | 2.943921 s | 0.173476 s | 0.453765 s |
| Median CPU, one-logical-CPU scale | 0.490465% | 0.028901% | 0.075594% |
| CPU range across 3 trials | 0.461732–0.503670% | 0.024271–0.034123% | 0.075474–0.091409% |
| Summed process RSS sampled | 130.1–219.0 MiB | 20.8–24.7 MiB | 26.4–28.6 MiB |
| Network | none | none | Docker bridge |
| DHT status | No DHT service in this comparison | Disabled | Enabled and bootstrapped before and after each window |
| Soulseek session, shares, transfers, UI/client traffic | None | None | None |

The CPU and memory fields use the same collection method. The DHT-on column
uses the same slskR image digest but ran later, with bridge networking and
higher recorded legacy host CPU busy (23.9%–47.7% versus 14.3%–21.9% for the
matched disconnected trials). The raw measurements do not isolate DHT
cost from network mode or host-time variation; the table is a profile
comparison, not a causal estimate of the CPU overhead from DHT alone.

### DHT-on trial details

| Repetition | CPU time | One-core CPU | RSS sample range | Recorded host CPU busy (legacy) | DHT routing nodes before → after | Discovered peers before → after |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 0.548808 s | 0.091409% | 28.5–28.6 MiB | 47.72% | 156 → 156 | 69 → 66 |
| 2 | 0.453765 s | 0.075594% | 28.2–28.3 MiB | 29.36% | 23 → 101 | 65 → 65 |
| 3 | 0.453027 s | 0.075474% | 26.4–26.9 MiB | 23.89% | 144 → 144 | 65 → 68 |

Legacy host-busy figures were collected before the runner excluded
guest and `guest_nice` ticks from `/proc/stat`; they may be overstated and
cannot be recomputed from the retained artifacts. Current reruns use the
corrected accounting.

The DHT status endpoint reported the service enabled and bootstrapped before
and after all three CPU windows. It reported a `lastError` value before trial
2, which was absent at the end of that trial; the error text was not retained.
No DHT status request was made during a CPU measurement window. Peer counts
are observations from separate fresh containers, not a controlled peer-count
match.

The DHT-on runner makes one authenticated status request immediately before
and one immediately after each CPU window. Those two local-only probes are
outside the measured interval and are not client/UI workload.

This is the closest reproducible “full-default idle” profile without account
credentials or a share dataset. It leaves other release-image settings at
their defaults, but does not exercise features that need a login, shares,
transfers, API/UI traffic, integration credentials, or other configured data.
There is no single switch that makes all such features active. A claim about
“all features enabled” would overstate this workload.

## Interpreting a reported 28% CPU value

This benchmark did not reproduce the reported 28%. If that figure came from
the standard Linux Docker CLI CPU calculation, 28% represents about 0.28 of
one logical CPU. The repeated slskd median here was 0.004905 of one logical
CPU, so 28% is about 57 times that measured value under the same CPU-unit
interpretation. Across the three slskd trials, the corresponding factor is
about 55.6x–60.6x.

Docker's CLI calculation derives container CPU percentage from the container
CPU-time delta divided by the system CPU-time delta, multiplied by the online
CPU count and 100 ([Docker CLI source](https://github.com/docker/cli/blob/master/cli/command/container/stats_helpers.go#L1063-L1094)). A NAS dashboard may use a
different denominator, such as a configured container quota. The monitoring
tool, its denominator/quota, and the target container's own cgroup counters
must be checked before comparing its displayed 28% with this result.

The earlier single-window pilot recorded 0.719143% of one logical CPU for
slskd and yielded a 36.5x CPU ratio. It used one 180-second window per image
after a 45-second warm-up. It is retained as historical diagnostic evidence,
not the primary result: the longer repeated run above is more informative, and
the pilot ratio should not be used as the headline.

## Images and host

The runner requested the published release images by immutable digest and
recorded the resolved image IDs:

| Project | Requested image | Image ID | Release source |
| --- | --- | --- | --- |
| slskR | `ghcr.io/snapetech/slskr@sha256:ec36112f5cf390e3c09a3ab1faf94f13786415cd184a401f0fa2e5ef5fe4c7a5` | `sha256:ec36112f5cf390e3c09a3ab1faf94f13786415cd184a401f0fa2e5ef5fe4c7a5` | [v0.2.56](https://github.com/snapetech/slskr/releases/tag/release-v0.2.56) |
| slskd | `slskd/slskd@sha256:588af49abc3088d639c8f1174d3bfad6e92c093a275a593140e3ac9311ebf6c4` | `sha256:588af49abc3088d639c8f1174d3bfad6e92c093a275a593140e3ac9311ebf6c4` | [0.26.1](https://github.com/slskd/slskd/releases/tag/0.26.1) |

Recorded host details:

- Linux 7.1.7-arch1-1, x86_64, 32 online CPUs and cgroup v2.
- Docker client 29.9.0 and server 29.8.0.
- Both images ran as `linux/amd64`.
- The host had unrelated workloads; load average and aggregate CPU activity
  are retained in the JSON artifact.

The [slskd 0.26.1 release](https://github.com/slskd/slskd/releases/tag/0.26.1)
enables disk logging by default. That default was left enabled, so this result
includes the release image's default logging behavior.

## Workload and configuration

The matched slskd and slskR containers used `--network none`; the DHT-on slskR
profile used Docker bridge networking so the DHT could reach peers. All
containers had Docker health checks disabled. During measured windows there
was no Soulseek login or server connection, transfer, shared root, share scan,
or UI/client API traffic. Each trial used a fresh container, ran alone, and
was removed after measurement. The DHT-on profile made authenticated status
probes only immediately before and after its CPU window.

slskR used:

- `SLSKR_AUTO_CONNECT=false`
- `SLSKR_DHT_ENABLED=false`
- `SLSKR_CREDENTIAL_STORE=memory`
- State directory `/tmp/slskr-idle-bench`

slskd used:

- `SLSKD_NO_CONNECT=true`
- `SLSKD_NO_SHARE_SCAN=true`
- The release-image default logging configuration

slskR's DHT was disabled explicitly. slskd has no corresponding DHT service
in this comparison. These settings intentionally isolate local disconnected
idle work; they do not match a connected user session.

The DHT-on profile uses the same image and state/credential setup with
`SLSKR_DHT_ENABLED=true`, Docker bridge networking, and an ephemeral host port
bound only to `127.0.0.1` for status verification. Soulseek auto-connect stays
disabled because no credentials are configured. Other image settings remain
at their release defaults; features needing accounts, shares, requests, or
transfers are not active workloads here.

## Reproducing the repeated run

The maintained runner is
[`benchmarks/compare-idle-containers.py`](../compare-idle-containers.py). It
requires Linux with cgroup v2, Docker access, and both pinned images available
locally or pullable. It starts fresh containers sequentially, reads cgroup
counters from the host, samples process RSS and cgroup memory once per minute,
and saves JSON after each trial. It does not stop, modify, or benchmark other
containers. Expect about 78 minutes for the defaults below.

```bash
python3 benchmarks/compare-idle-containers.py \
  --repeats 3 \
  --warmup-seconds 180 \
  --duration-seconds 600 \
  --sample-interval-seconds 60 \
  --output target/perf/20261012-idle-container-repeats.json
```

Reproduction output goes to the ignored `target/perf/` directory so an
interrupted or failed run cannot replace the checked-in measurement artifact.
The runner creates the output directory when needed.

The complete recorded output is
[`20261012-idle-container-repeats.json`](20261012-idle-container-repeats.json)
(SHA-256 `b0e55c23bb5bec9b46976aa28ca9d0d8445d78e0537684d41b5ae0d5817969e0`).
It includes image identities, timestamps, trial order, all cgroup CPU counters,
host CPU activity/load, and all memory samples. Preserve the JSON with any
quotation or follow-up comparison so the rounded report values can be checked.

The DHT-on profile was measured separately with the same runner:

```bash
python3 benchmarks/compare-idle-containers.py \
  --profiles slskr-dht \
  --repeats 3 \
  --warmup-seconds 180 \
  --duration-seconds 600 \
  --sample-interval-seconds 60 \
  --output target/perf/20261012-idle-container-slskr-dht.json
```

The retained [DHT-on JSON](20261012-idle-container-slskr-dht.json) has SHA-256
`f8889185dc1b7b3b8b4e67bd76abb01a3018847fbbfee219aa0f43d87728f9ed`. The
archived sample predates per-run API-token hardening. Current reruns bind the
HTTP status endpoint inside the container, publish an ephemeral port only on
host loopback, and create a fresh random API token for each trial without
recording it in the artifact. The runner queries `/api/dht/status` after
warm-up and after CPU measurement, never during the measured window.

## What would make the next comparison stronger

This is a sounder baseline than one short sample, but it is not the most
complete test of the reported NAS behavior. The next measurements that would
add the most evidence are:

1. **Reproduce the reported container.** Record the exact image digest, NAS
   model/CPU architecture, Docker or NAS monitor name, CPU quota/cpuset,
   cgroup `cpu.stat`, and monitor values over the same 10-minute interval.
   This can determine whether 28% is a real cgroup CPU load or a display-unit
   mismatch.
2. **Connected idle.** Run both release images with a logged-in session, no
   transfers, the same share roots and completed scan state, and the same UI/API
   polling pattern. Keep product-default logging, record config, and repeat
   fresh runs. This is closer to “idle with no uploads/downloads.”
3. **Representative activity.** If the reporter's concern includes the
   library, add equal share datasets and a separately labeled initial/rescan
   scenario. Keep scanning distinct from steady idle.
4. **Memory accounting.** Capture PSS with permission to read each process's
   `smaps_rollup`, alongside summed RSS and cgroup `memory.current`/`memory.stat`.
   Use the same monitoring field the NAS UI displays.
5. **More hosts and repetitions.** Repeat on the NAS CPU architecture and on a
   second quiet host, with more randomized trial order. Keep each host's raw
   results separate; do not pool unlike hardware into one ratio.
6. **Network-mode control.** To estimate DHT's incremental cost separately,
   add slskR with DHT disabled but bridge networking and the same local API
   status instrumentation. The current DHT-on column cannot separate those
   factors.

Those follow-ups need the reporter's exact environment and settings. Until
then, the defensible statement is limited to the pinned images and the
disconnected-idle conditions measured here. These measurements do not identify
why another system reports a different value or establish the cause of any
observed difference.
