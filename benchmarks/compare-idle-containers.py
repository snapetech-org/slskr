#!/usr/bin/env python3
"""Repeat an isolated idle comparison of the pinned slskR and slskd images.

CPU and memory cgroup counters are read from the host cgroup filesystem. The
measurement does not launch docker exec processes inside the containers.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import random
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


IMAGES = {
    "slskr": "ghcr.io/snapetech/slskr@sha256:ec36112f5cf390e3c09a3ab1faf94f13786415cd184a401f0fa2e5ef5fe4c7a5",
    "slskd": "slskd/slskd@sha256:588af49abc3088d639c8f1174d3bfad6e92c093a275a593140e3ac9311ebf6c4",
    "slskr-dht": "ghcr.io/snapetech/slskr@sha256:ec36112f5cf390e3c09a3ab1faf94f13786415cd184a401f0fa2e5ef5fe4c7a5",
}
NETWORKS = {"slskr": "none", "slskd": "none", "slskr-dht": "bridge"}
CGROUP_ROOT = Path("/sys/fs/cgroup")
DHT_API_TOKEN = "idle-benchmark-local-token-2026"
SLSKD_API_KEY = "idle-benchmark-local-api-key-2026"
SLSKD_API_KEY_CONFIG = (
    f"role=ReadOnly;cidr=0.0.0.0/0,::/0;{SLSKD_API_KEY}"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def docker(*args: str, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        ["docker", *args], check=True, capture_output=True, text=True, env=env
    )
    return result.stdout.strip()


def key_values(path: Path) -> dict[str, int]:
    values: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, value = line.split()[:2]
        try:
            values[key] = int(value)
        except ValueError:
            continue
    return values


def host_cpu_ticks() -> dict[str, int]:
    line = next(
        row for row in Path("/proc/stat").read_text().splitlines()
        if row.startswith("cpu ")
    )
    values = [int(value) for value in line.split()[1:]]
    return {
        "total": sum(values),
        "idle": values[3] + (values[4] if len(values) > 4 else 0),
    }


def host_cpu_busy_percent(start: dict[str, int], end: dict[str, int]) -> float:
    total_delta = end["total"] - start["total"]
    idle_delta = end["idle"] - start["idle"]
    return 100.0 * (total_delta - idle_delta) / total_delta if total_delta else 0.0


def process_memory(container: str) -> dict[str, Any]:
    output = docker("top", container, "-eo", "pid")
    pids = [int(line.strip()) for line in output.splitlines()[1:] if line.strip().isdigit()]
    rss_kib = 0
    pss_kib = 0
    pss_complete = True
    for pid in pids:
        status = Path(f"/proc/{pid}/status")
        try:
            for line in status.read_text().splitlines():
                if line.startswith("VmRSS:"):
                    rss_kib += int(line.split()[1])
                    break
            rollup = Path(f"/proc/{pid}/smaps_rollup").read_text()
            pss_line = next(line for line in rollup.splitlines() if line.startswith("Pss:"))
            pss_kib += int(pss_line.split()[1])
        except (FileNotFoundError, PermissionError, StopIteration, ValueError):
            pss_complete = False
    return {
        "process_count": len(pids),
        "rss_kib_sum": rss_kib,
        "pss_kib_sum": pss_kib if pss_complete else None,
        "pss_complete": pss_complete,
    }


def cgroup_for_container(container: str) -> Path:
    init_pid = int(docker("inspect", "--format", "{{.State.Pid}}", container))
    entries = Path(f"/proc/{init_pid}/cgroup").read_text().splitlines()
    unified = next((line.partition("::")[2] for line in entries if "::" in line), None)
    if unified is None:
        raise RuntimeError("container process is not in a cgroup v2 hierarchy")
    path = (CGROUP_ROOT / unified.lstrip("/")).resolve()
    if not path.is_relative_to(CGROUP_ROOT.resolve()):
        raise RuntimeError(f"container cgroup path escaped {CGROUP_ROOT}")
    return path


def memory_snapshot(container: str, cgroup: Path) -> dict[str, Any]:
    memory_stat = key_values(cgroup / "memory.stat")
    return {
        "time_utc": utc_now(),
        "memory_current_bytes": int((cgroup / "memory.current").read_text()),
        "memory_stat_bytes": {
            key: memory_stat[key]
            for key in ("anon", "file", "shmem", "kernel", "slab")
            if key in memory_stat
        },
        **process_memory(container),
    }


def image_info(image: str) -> dict[str, Any]:
    raw = docker("image", "inspect", image, "--format", "{{json .}}")
    value = json.loads(raw)
    return {
        "requested": image,
        "image_id": value.get("Id"),
        "repo_digests": value.get("RepoDigests", []),
        "platform": f"{value.get('Os')}/{value.get('Architecture')}",
    }


def run_command(
    app: str,
    container: str,
    *,
    live_session: bool = False,
) -> list[str]:
    command = [
        "run", "--rm", "-d", "--name", container,
        "--platform", "linux/amd64",
        "--network", "bridge" if live_session else NETWORKS[app],
        "--no-healthcheck",
    ]
    if app in ("slskr", "slskr-dht"):
        command.extend([
            "-e", f"SLSKR_AUTO_CONNECT={'true' if live_session else 'false'}",
            "-e", f"SLSKR_DHT_ENABLED={'true' if app == 'slskr-dht' else 'false'}",
            "-e", "SLSKR_CREDENTIAL_STORE=memory",
            "-e", f"SLSKR_STATE_DIR=/tmp/slskr-{'live-' if live_session else ''}idle-bench",
        ])
        if live_session:
            command.extend([
                "-p", "127.0.0.1::5030/tcp",
                "-e", "SLSKR_HTTP_BIND=0.0.0.0:5030",
                "-e", "SLSKR_API_TOKEN",
                "-e", "SLSKD_SLSK_USERNAME",
                "-e", "SLSKD_SLSK_PASSWORD",
                "-e", "SLSKD_SLSK_ADDRESS=vps.slsknet.org",
                "-e", "SLSKD_SLSK_PORT=2271",
                "-e", "SLSKD_NO_SHARE_SCAN=true",
            ])
        elif app == "slskr-dht":
            command.extend([
                "-p", "127.0.0.1::5030/tcp",
                "-e", "SLSKR_HTTP_BIND=0.0.0.0:5030",
                "-e", f"SLSKR_API_TOKEN={DHT_API_TOKEN}",
            ])
    else:
        if live_session:
            command.extend([
                "-p", "127.0.0.1::5030/tcp",
                "-e", "SLSKD_SLSK_USERNAME",
                "-e", "SLSKD_SLSK_PASSWORD",
                "-e", "SLSKD_SLSK_ADDRESS=vps.slsknet.org",
                "-e", "SLSKD_SLSK_PORT=2271",
                "-e", "SLSKD_API_KEY",
                "-e", "SLSKD_NO_CONNECT=false",
                "-e", "SLSKD_NO_SHARE_SCAN=true",
            ])
        else:
            command.extend([
                "-e", "SLSKD_NO_CONNECT=true",
                "-e", "SLSKD_NO_SHARE_SCAN=true",
            ])
    command.append(IMAGES[app])
    return command


def local_api_json(
    container: str,
    path: str,
    auth: tuple[str, str] | None = None,
) -> dict[str, Any]:
    mapping = docker("port", container, "5030/tcp").splitlines()[0].strip()
    host_port = int(mapping.rsplit(":", 1)[1])
    headers = {"Accept": "application/json"}
    if auth is not None:
        headers[auth[0]] = auth[1]
    request = urllib.request.Request(
        f"http://127.0.0.1:{host_port}{path}", headers=headers
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        value = json.load(response)
    if not isinstance(value, dict):
        raise RuntimeError("local status endpoint returned a non-object response")
    return value


def dht_runtime_status(container: str) -> dict[str, Any]:
    status = local_api_json(
        container,
        "/api/dht/status",
        ("Authorization", f"Bearer {DHT_API_TOKEN}"),
    )
    return {
        "enabled": status.get("isEnabled"),
        "bootstrapped": status.get("bootstrapped"),
        "running": status.get("isDhtRunning"),
        "routing_node_count": status.get("dhtNodeCount"),
        "discovered_peer_count": status.get("discoveredPeerCount"),
        "last_error_present": bool(status.get("lastError")),
    }


def soulseek_runtime_status(container: str, app: str) -> dict[str, Any]:
    auth = (
        ("X-API-Key", SLSKD_API_KEY)
        if app == "slskd"
        else ("Authorization", f"Bearer {DHT_API_TOKEN}")
    )
    status = local_api_json(
        container,
        "/api/v0/server",
        auth,
    )
    logged_in = status.get("isLoggedIn") is True
    return {
        "connected": status.get("isConnected") is True or logged_in,
        "logged_in": logged_in,
        "state": status.get("state") if isinstance(status.get("state"), str) else None,
    }


def wait_for_soulseek_login(
    container: str, app: str, timeout_seconds: int
) -> tuple[dict[str, Any], float, int]:
    started = time.monotonic()
    attempts = 0
    last_status: dict[str, Any] = {"connected": False, "logged_in": False, "state": None}
    while time.monotonic() - started < timeout_seconds:
        attempts += 1
        try:
            last_status = soulseek_runtime_status(container, app)
            if last_status["logged_in"]:
                return last_status, time.monotonic() - started, attempts
        except (OSError, RuntimeError, ValueError, urllib.error.URLError):
            pass
        time.sleep(5)
    return last_status, time.monotonic() - started, attempts


def run_trial(
    app: str,
    repetition: int,
    warmup: int,
    duration: int,
    interval: int,
    *,
    live_session: bool = False,
    credentials: tuple[str, str] | None = None,
    login_timeout: int = 300,
) -> dict[str, Any]:
    prefix = "liveidle" if live_session else "idlecmp"
    container = f"{prefix}-{app}-{repetition:02d}"
    started = utc_now()
    child_env = None
    if live_session:
        if credentials is None:
            raise RuntimeError("live-session mode requires test credentials")
        child_env = os.environ.copy()
        child_env["SLSKD_SLSK_USERNAME"] = credentials[0]
        child_env["SLSKD_SLSK_PASSWORD"] = credentials[1]
        child_env["SLSKR_API_TOKEN"] = DHT_API_TOKEN
        child_env["SLSKD_API_KEY"] = SLSKD_API_KEY_CONFIG
    docker(
        *run_command(app, container, live_session=live_session),
        env=child_env,
    )
    try:
        cgroup = cgroup_for_container(container)
        cpu_limit = (cgroup / "cpu.max").read_text().strip()
        login_ready = None
        login_wait_seconds = None
        login_attempts = None
        if live_session:
            print(f"{container}: waiting for a live Soulseek login", flush=True)
            login_ready, login_wait_seconds, login_attempts = wait_for_soulseek_login(
                container, app, login_timeout
            )
            if not login_ready["logged_in"]:
                raise RuntimeError(
                    f"{container} did not reach authenticated Soulseek state within {login_timeout} seconds"
                )
            print(
                f"{container}: authenticated session ready after {login_wait_seconds:.1f}s; "
                f"warm-up {warmup}s",
                flush=True,
            )
        else:
            print(f"{container}: warm-up {warmup}s", flush=True)
        time.sleep(warmup)

        session_status_before = soulseek_runtime_status(container, app) if live_session else None
        if live_session and not session_status_before["logged_in"]:
            raise RuntimeError(f"{container} lost its Soulseek login during warm-up")
        if live_session and app in ("slskr", "slskr-dht"):
            dht_status_before = dht_runtime_status(container)
        else:
            dht_status_before = dht_runtime_status(container) if app == "slskr-dht" else None
        load_start = os.getloadavg()
        cpu_start = key_values(cgroup / "cpu.stat")
        host_start = host_cpu_ticks()
        wall_start = time.monotonic()
        memory_samples = [memory_snapshot(container, cgroup)]
        elapsed = 0
        while elapsed < duration:
            wait = min(interval, duration - elapsed)
            time.sleep(wait)
            elapsed += wait
            memory_samples.append(memory_snapshot(container, cgroup))
            print(f"{container}: sampled {elapsed}/{duration}s", flush=True)

        cpu_end = key_values(cgroup / "cpu.stat")
        wall_end = time.monotonic()
        host_end = host_cpu_ticks()
        session_status_after = soulseek_runtime_status(container, app) if live_session else None
        if live_session and app in ("slskr", "slskr-dht"):
            dht_status_after = dht_runtime_status(container)
        else:
            dht_status_after = dht_runtime_status(container) if app == "slskr-dht" else None
        wall_seconds = wall_end - wall_start
        usage_delta = cpu_end["usage_usec"] - cpu_start["usage_usec"]
        trial = {
            "app": app,
            "repetition": repetition,
            "container_started_utc": started,
            "measurement_started_utc": memory_samples[0]["time_utc"],
            "warmup_seconds": warmup,
            "requested_window_seconds": duration,
            "actual_wall_seconds": wall_seconds,
            "cpu_limit": cpu_limit,
            "cpu_stat_start": cpu_start,
            "cpu_stat_end": cpu_end,
            "cpu_usage_delta_usec": usage_delta,
            "cpu_seconds": usage_delta / 1_000_000,
            "average_one_core_percent": 100 * usage_delta / (wall_seconds * 1_000_000),
            "host_cpu_busy_percent": host_cpu_busy_percent(host_start, host_end),
            "host_load_average_start": load_start,
            "host_load_average_end": os.getloadavg(),
            "live_session": live_session,
            "session_login_wait_seconds": login_wait_seconds,
            "session_login_status_attempts": login_attempts,
            "session_status_before": session_status_before,
            "session_status_after": session_status_after,
            "session_logged_in_at_measurement_boundaries": (
                bool(session_status_before and session_status_before["logged_in"])
                and bool(session_status_after and session_status_after["logged_in"])
                if live_session else None
            ),
            "dht_status_before": dht_status_before,
            "dht_status_after": dht_status_after,
            "memory_samples": memory_samples,
        }
        print(json.dumps({
            "trial": f"{app}-{repetition}",
            "cpu_seconds": trial["cpu_seconds"],
            "one_core_percent": trial["average_one_core_percent"],
            "host_cpu_busy_percent": trial["host_cpu_busy_percent"],
            "memory_start": memory_samples[0]["memory_current_bytes"],
            "memory_end": memory_samples[-1]["memory_current_bytes"],
        }), flush=True)
        return trial
    finally:
        stopped = subprocess.run(
            ["docker", "stop", "--time", "10", container],
            capture_output=True,
            text=True,
        )
        if stopped.returncode != 0:
            subprocess.run(
                ["docker", "rm", "-f", container],
                capture_output=True,
                text=True,
            )


def save(path: Path, result: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--warmup-seconds", type=int, default=180)
    parser.add_argument("--duration-seconds", type=int, default=600)
    parser.add_argument("--sample-interval-seconds", type=int, default=60)
    parser.add_argument(
        "--profiles", nargs="+", choices=sorted(IMAGES), default=["slskr", "slskd"],
        help="profiles to run; slskr-dht enables DHT and external bridge networking",
    )
    parser.add_argument(
        "--live-session", action="store_true",
        help="connect profiles to the public Soulseek server with credentials from the named environment variables",
    )
    parser.add_argument(
        "--credential-username-env", default="SLSKR_LIVE_BENCH_USERNAME",
        help="host environment variable containing the test account username",
    )
    parser.add_argument(
        "--credential-password-env", default="SLSKR_LIVE_BENCH_PASSWORD",
        help="host environment variable containing the test account password",
    )
    parser.add_argument("--login-timeout-seconds", type=int, default=300)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.repeats < 1 or args.warmup_seconds < 0 or args.duration_seconds < 1 or args.sample_interval_seconds < 1:
        raise SystemExit("repeats and durations must be positive; warm-up may be zero")
    if args.login_timeout_seconds < 1:
        raise SystemExit("login timeout must be positive")
    if platform.system() != "Linux" or not (CGROUP_ROOT / "cgroup.controllers").exists():
        raise SystemExit("this runner requires Linux with cgroup v2")
    prefix = "liveidle" if args.live_session else "idlecmp"
    if docker("ps", "--filter", f"name=^/{prefix}-", "--format", "{{.Names}}"):
        raise SystemExit(f"a {prefix}-* container is already running")

    credentials = None
    if args.live_session:
        username = os.environ.get(args.credential_username_env, "")
        password = os.environ.get(args.credential_password_env, "")
        if not username or not password:
            raise SystemExit(
                "live-session credentials are missing from the named environment variables"
            )
        credentials = (username, password)

    order: list[str] = []
    for repetition in range(1, args.repeats + 1):
        shift = (repetition - 1) % len(args.profiles)
        profiles = args.profiles[shift:] + args.profiles[:shift]
        order.extend(profiles)
    result: dict[str, Any] = {
        "schema_version": 1,
        "started_utc": utc_now(),
        "parameters": {
            "repeats_per_app": args.repeats,
            "warmup_seconds": args.warmup_seconds,
            "duration_seconds": args.duration_seconds,
            "memory_sample_interval_seconds": args.sample_interval_seconds,
            "profiles": args.profiles,
            "order": order,
            "network": (
                "bridge" if args.live_session else
                "none" if all(NETWORKS[app] == "none" for app in args.profiles) else
                "profile-dependent"
            ),
            "network_by_profile": {
                app: "bridge" if args.live_session else NETWORKS[app]
                for app in args.profiles
            },
            "live_soulseek_session": args.live_session,
            "credentials": (
                "same test account reused sequentially; values omitted"
                if args.live_session else "not configured"
            ),
            "server_endpoint": "vps.slsknet.org:2271" if args.live_session else None,
            "share_scan_disabled": args.live_session,
            "healthchecks": False,
            "cpu_accounting": "host-read cgroup v2 cpu.stat usage_usec",
        },
        "host": {
            "platform": platform.platform(),
            "architecture": platform.machine(),
            "kernel": platform.release(),
            "online_cpus": os.cpu_count(),
            "process_cpu_affinity_count": len(os.sched_getaffinity(0)),
            "cgroup_version": "v2",
            "docker_version": docker("version", "--format", "client={{.Client.Version}} server={{.Server.Version}}"),
            "load_average_at_start": os.getloadavg(),
        },
        "images": {app: image_info(IMAGES[app]) for app in args.profiles},
        "trials": [],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    save(args.output, result)
    print(
        f"Starting {len(order)} sequential fresh-container trials; "
        f"live Soulseek session: {args.live_session}; output: {args.output}",
        flush=True,
    )
    for index, app in enumerate(order, start=1):
        repetition = order[:index].count(app)
        trial = run_trial(
            app,
            repetition,
            args.warmup_seconds,
            args.duration_seconds,
            args.sample_interval_seconds,
            live_session=args.live_session,
            credentials=credentials,
            login_timeout=args.login_timeout_seconds,
        )
        result["trials"].append(trial)
        result["updated_utc"] = utc_now()
        result["host"]["load_average_at_end"] = os.getloadavg()
        save(args.output, result)
    result["completed_utc"] = utc_now()
    save(args.output, result)
    print(f"Completed {len(result['trials'])} trials: {args.output}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
