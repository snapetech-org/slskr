# Live Soulseek connected-idle comparison (2026-10-12)

## Scope and confidence

This diagnostic run compares pinned slskd and slskR release images while each
client is authenticated to the Soulseek server and otherwise idle. The valid
completed matrix was measured on `kspld0`. A separate `kspls0` attempt was
aborted after severe host CPU saturation was observed; it produced no valid
trial and is not included in the results below.

**Confidence:** high that the reported `kspld0` CPU values match the recorded
cgroup v2 counters; moderate that the three profile medians describe this
host and workload; low for predicting a different host, configuration, or
active workload. The DHT-on profile returned a DHT error indicator at the end
of one trial, which is called out below.

The result is a measurement of these image versions, settings, account
session, endpoint, and host conditions. It does not establish that the
reporter's 28% reading was wrong: their host, container quota, configuration,
and monitor denominator were not available for this run.

## Results: `kspld0`

Each value summarizes authenticated windows only. CPU time is the change in
container cgroup `cpu.stat` `usage_usec`; one-core percent is CPU time divided
by the actual measured wall time. A value of 100% on this scale means one
logical CPU was occupied for the whole window.

| Measurement | slskd 0.26.1, connected idle | slskR v0.2.56, DHT off | slskR v0.2.56, DHT on |
| --- | ---: | ---: | ---: |
| Valid authenticated windows | 3 of 5 attempts | 3 of 3 | 3 of 3 |
| Median CPU time per 600 s | 16.852206 s | 0.555272 s | 0.758278 s |
| CPU-time range | 16.746842–17.801291 s | 0.362794–0.573935 s | 0.730970–0.809699 s |
| Median one-logical-CPU use | 2.807641% | 0.092509% | 0.126304% |
| One-core range | 2.790171–2.964597% | 0.060440–0.095614% | 0.121780–0.134902% |
| Process RSS sampled during valid windows | 196.9–262.7 MiB | 10.0–28.5 MiB | 28.9–29.6 MiB |
| Cgroup `memory.current` samples | 162.2–320.9 MiB | 5.6–57.5 MiB | 5.7–58.5 MiB |

The `memory.current` row is the cgroup charge, including file cache and other
charged memory; it is not process RSS. RSS is the sum of resident memory for
processes in the container and can count shared pages more than once. Both
memory figures are sampled at one-minute intervals, not continuous peaks.

The local host had 32 logical CPUs, Linux 7.1.7-arch1-1, Docker client 29.9.0,
Docker server 29.8.0, and cgroup v2. Recorded (legacy) aggregate host CPU busy
percentages during valid windows ranged from 17.77% to 46.76%; per-trial
start/end load averages are in the raw JSON. The host was not idle, and its
load varied across these sequential trials.

These archived host-busy percentages were collected before the runner excluded
guest and `guest_nice` ticks from `/proc/stat`. Linux already includes those
ticks in user and nice, so the figures may be overstated. The raw artifacts do
not retain the individual host tick deltas needed to recompute them; current
reruns use the corrected accounting.

### Trial validity notes

- `slskd` attempts 1 and 3 in the main artifact and the separate replacement
  trial both had an authenticated session before and after measurement. The
  main artifact's `slskd` repetition 2 used 14.327459 CPU seconds, but the
  session was no longer logged in at the end, so it is preserved as an
  invalid trial and excluded from the table. The replacement is retained in a
  separate raw file rather than substituted into the original sequence. A
  fifth, metadata-only `slskd` retry attempt started but produced no completed
  trial; it is included in the attempt denominator and preserved separately.
- All three DHT-off slskR windows had an authenticated session at both
  boundaries.
- All three DHT-on windows had an authenticated Soulseek session, and DHT was
  enabled, running, and bootstrapped at both boundary checks. At the end of
  DHT-on repetition 3, however, the status also reported a last-error
  indicator and zero discovered peers. The error text was not retained. The
  table's DHT-on median includes all three session-valid windows; the median
  of the two windows with no DHT error indicator at either boundary is
  0.783989 CPU seconds (0.130665% of one logical CPU). Neither figure isolates
  the causal cost of DHT.

### Supplemental DHT-on retry

After the primary matrix, one separate DHT-on window completed on `kspld0`.
The authenticated session was valid at both measurement boundaries, and DHT
was enabled, running, and bootstrapped at both status checks. The initial DHT
status carried a last-error indicator with 71 discovered peers; the indicator
was clear at the end, with 69 discovered peers. It used 0.664036 CPU seconds
over 600.214 seconds (0.110633% of one logical CPU); recorded (legacy) host
CPU busy was 21.76% during the window. This single supplemental trial is kept separate
from the three-window DHT-on median above. Its host load samples and complete
metadata are in the [supplemental DHT-on retry artifact](20261012-live-soulseek-slskr-dht-retry.json).

## Attempted second host: `kspls0`

No `kspls0` result is reported. The host has 32 logical CPUs and the LVM data
pool at `/mnt/datapool_lvm_media`; this path is also mounted on `kspld0` from
`kspls0:/mnt/datapool_lvm_media` over NFSv4.2. The pool reported about 31 TiB
available during this run.

The first `slskd` attempt reached its first 60-second memory sample, but the
host was severely CPU-saturated. At 2026-10-12 20:53 UTC, the host reported a
load average of 195.35, 120.61, and 104.35; two consecutive one-second
`vmstat` samples showed 0% idle CPU and 237 then 275 runnable tasks. I stopped
the task-owned benchmark container. The runner then could not read that
container's removed cgroup and did not save a completed trial. The attempt is
retained in [`kspls0 aborted-run metadata`](20261012-live-soulseek-idle-kspls0-aborted.json)
with zero completed trials. No other containers or services were stopped.

Because that environment was saturated, this report makes no cross-host
comparison and no `kspls0` CPU or memory claim. A second-host matrix needs a
separate run under recorded, materially less saturated conditions.

## Method

- Profiles: slskd 0.26.1; slskR v0.2.56 with DHT disabled; and the same slskR
  image with DHT enabled. All profiles used Docker bridge networking and the
  same Soulseek endpoint, `vps.slsknet.org:2271`.
- One dedicated test account was reused sequentially. The runner did not
  overlap client sessions. Each repetition used a fresh container; profile
  order rotated between repetitions to reduce simple time-order bias.
- Each container warmed up for 180 seconds after login, then ran for a
  requested 600-second measurement window. Memory was sampled every 60
  seconds. The runner recorded actual wall time and read cgroup v2 counters
  from the host, not with `docker exec`.
- The runner verified authenticated session state immediately before and
  after each CPU window. For DHT-on, it also checked DHT state at those
  boundaries. These probes were outside the measured windows; there were no
  API/UI requests during measurement.
- Share scanning was disabled. No share roots, searches, transfers, or other
  feature workloads were configured or exercised. “DHT on” means the DHT
  service was enabled for this idle profile; it does not mean every slskR
  feature was configured and under load.
- The same pinned release images were used throughout. The kspld0 runner
  requested the slskR image by repository digest. For the aborted kspls0
  attempt, the exact locally verified slskR image was transferred with
  `docker save`/`docker load` after GHCR denied a direct pull; the loaded image
  ID matched the verified digest. The slskd digest was pulled directly.
- Credentials are omitted from the JSON artifacts. The test credential file
  on `kspls0` was mode 600 and removed by the remote launcher after the
  attempt.

## Raw artifacts and reproducibility

- [Primary `kspld0` matrix, including the invalid slskd repetition](20261012-live-soulseek-idle-matrix.json)
- [Authenticated slskd replacement trial](20261012-live-soulseek-slskd-retry-2.json)
- [Metadata-only earlier slskd retry attempt](20261012-live-soulseek-slskd-retry.json)
- [Supplemental DHT-on retry trial](20261012-live-soulseek-slskr-dht-retry.json)
- [Aborted `kspls0` attempt metadata](20261012-live-soulseek-idle-kspls0-aborted.json)
- [Runner](../compare-idle-containers.py)

The CPU figures are specific observations, not a universal ranking, a
production claim, or a reproduction of another operator's dashboard reading.
