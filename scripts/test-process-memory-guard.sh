#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

expected_fallback_limit="262144"
if [[ "$(uname -s)" == "Darwin" ]]; then
  expected_fallback_limit="unlimited"
fi

guard=scripts/with-process-memory-guard.sh

if SLSKR_PROCESS_MEMORY_MAX_KIB=4194305 \
  "$guard" bash -c 'exit 0' >/dev/null 2>&1; then
  printf 'Process memory guard test failed: over-limit memory was accepted\n' >&2
  exit 1
fi

fallback_limit="$(
  SLSKR_PROCESS_MEMORY_GUARD_DISABLE_SYSTEMD=1 \
  SLSKR_PROCESS_MEMORY_MAX_KIB=262144 \
    "$guard" bash -c 'ulimit -v'
)"
if [[ "$fallback_limit" != "$expected_fallback_limit" ]]; then
  printf 'Process memory guard test failed: fallback limit was %s\n' "$fallback_limit" >&2
  exit 1
fi

spoofed_marker_limit="$(
  SLSKR_PROCESS_MEMORY_GUARD_DISABLE_SYSTEMD=1 \
  SLSKR_PROCESS_MEMORY_MAX_KIB=262144 \
  SLSKR_PROCESS_MEMORY_GUARD_HELD=1 \
    "$guard" bash -c 'ulimit -v'
)"
if [[ "$spoofed_marker_limit" != "$expected_fallback_limit" ]]; then
  printf 'Process memory guard test failed: externally supplied nesting marker bypassed the limit: %s\n' "$spoofed_marker_limit" >&2
  exit 1
fi

fallback_marker="$(
  SLSKR_PROCESS_MEMORY_GUARD_DISABLE_SYSTEMD=1 \
    "$guard" bash -c 'printf "%s" "$SLSKR_PROCESS_MEMORY_GUARD_HELD"'
)"
if [[ "$fallback_marker" != "1" ]]; then
  printf 'Process memory guard test failed: fallback nesting marker was %s\n' "$fallback_marker" >&2
  exit 1
fi

node_options="$(
  SLSKR_PROCESS_MEMORY_GUARD_DISABLE_SYSTEMD=1 \
    "$guard" node -e 'process.stdout.write(process.env.NODE_OPTIONS || "")'
)"
if [[ "$node_options" != *--max-old-space-size=1024* ]]; then
  printf 'Process memory guard test failed: Node heap cap was not installed\n' >&2
  exit 1
fi

expected_working_directory="$(node -e 'process.stdout.write(process.cwd())')"
working_directory="$(
  "$guard" node -e 'process.stdout.write(process.cwd())'
)"
if [[ "$working_directory" != "$expected_working_directory" ]]; then
  printf 'Process memory guard test failed: working directory was %s\n' "$working_directory" >&2
  exit 1
fi

forwarded_environment="$(
  SLSKDN_BINARY_PATH=/tmp/frozen-slskdn \
  SLSKR_CROSS_CLIENT_INDEX=bounded \
    "$guard" bash -c 'printf "%s|%s|%s" "$SLSKDN_BINARY_PATH" "$SLSKR_CROSS_CLIENT_INDEX" "$SLSKR_PROCESS_MEMORY_GUARD_HELD"'
)"
if [[ "$forwarded_environment" != "/tmp/frozen-slskdn|bounded|1" ]]; then
  printf 'Process memory guard test failed: caller environment was not forwarded: %s\n' "$forwarded_environment" >&2
  exit 1
fi

# A verified fallback may be reused, but a tighter nested request must apply.
nested_fallback_limit="$(
  SLSKR_PROCESS_MEMORY_GUARD_DISABLE_SYSTEMD=1 \
  SLSKR_PROCESS_MEMORY_MAX_KIB=262144 \
    "$guard" bash -c 'SLSKR_PROCESS_MEMORY_MAX_KIB=131072 "$1" bash -c "ulimit -v"' _ "$guard"
)"
expected_nested_limit=131072
if [[ "$(uname -s)" == "Darwin" ]]; then
  expected_nested_limit=unlimited
fi
if [[ "$nested_fallback_limit" != "$expected_nested_limit" ]]; then
  printf 'Process memory guard test failed: tighter nested limit was %s\n' "$nested_fallback_limit" >&2
  exit 1
fi

# Linux cgroup nesting must retain real memory/swap limits without RLIMIT_AS.
if [[ "$(uname -s)" == "Linux" ]] \
  && command -v systemd-run >/dev/null 2>&1 \
  && systemctl --user show-environment >/dev/null 2>&1 \
  && [[ "${SLSKR_PROCESS_MEMORY_GUARD_DISABLE_SYSTEMD:-0}" != "1" ]]; then
  nested_cgroup_limit="$(
    "$guard" bash -c '"$1" bash -c "ulimit -v"' _ "$guard"
  )"
  if [[ "$nested_cgroup_limit" != "unlimited" ]]; then
    printf 'Process memory guard test failed: verified cgroup gained virtual limit %s\n' "$nested_cgroup_limit" >&2
    exit 1
  fi
fi

# Hosted Linux runners usually have a system manager but no user manager.
# Exercise that route when passwordless sudo is available: V8 must retain its
# normal virtual address space while the cgroup enforces resident memory.
if [[ "$(uname -s)" == "Linux" ]] \
  && command -v sudo >/dev/null 2>&1 \
  && sudo -n systemctl show-environment >/dev/null 2>&1; then
  system_manager_node_output="$(
    SLSKR_PROCESS_MEMORY_GUARD_FORCE_SYSTEM_MANAGER=1 \
      "$guard" node -e '
const { execFileSync } = require("node:child_process");
const { readFileSync } = require("node:fs");

const cgroup = readFileSync("/proc/self/cgroup", "utf8")
  .split("\n")
  .find((line) => line.startsWith("0::"))
  ?.slice(3);
if (!cgroup || cgroup.includes("..")) {
  throw new Error("systemd memory cgroup path is missing or unsafe");
}
let memoryMax;
let memorySwapMax;
try {
  memoryMax = readFileSync(`/sys/fs/cgroup${cgroup}/memory.max`, "utf8").trim();
  memorySwapMax = readFileSync(`/sys/fs/cgroup${cgroup}/memory.swap.max`, "utf8").trim();
} catch (error) {
  if (error.code !== "ENOENT") throw error;
  const unit = process.env.SLSKR_PROCESS_MEMORY_GUARD_UNIT;
  if (!unit) {
    throw new Error("systemd memory cgroup files are not visible and the unit name is unavailable");
  }
  const properties = execFileSync("sudo", [
    "-n", "systemctl", "show", "--property=MemoryMax", "--property=MemorySwapMax", unit,
  ], { encoding: "utf8" });
  memoryMax = properties.match(/^MemoryMax=(.+)$/mu)?.[1];
  memorySwapMax = properties.match(/^MemorySwapMax=(.+)$/mu)?.[1];
}
if (!/^\d+$/u.test(memoryMax || "") || Number(memoryMax) > 4194304 * 1024) {
  throw new Error(`systemd memory cgroup has unexpected limit: ${memoryMax}`);
}
if (!/^\d+$/u.test(memorySwapMax || "") || Number(memorySwapMax) !== 0) {
  throw new Error(`systemd memory cgroup has unexpected swap limit: ${memorySwapMax}`);
}
const virtualMemoryLimit = execFileSync("bash", ["-c", "ulimit -v"], {
  encoding: "utf8",
}).trim();
if (virtualMemoryLimit !== "unlimited") {
  throw new Error(`systemd fallback applied RLIMIT_AS: ${virtualMemoryLimit}`);
}
const wasmMemory = new WebAssembly.Memory({ initial: 4096 });
new Uint8Array(wasmMemory.buffer).fill(1);
process.stdout.write("SYSTEMD_NODE_MEMORY_BOUNDARY_PASSED");
'
  )"
  if [[ "$system_manager_node_output" != "SYSTEMD_NODE_MEMORY_BOUNDARY_PASSED" ]]; then
    printf 'Process memory guard test failed: system manager Node boundary was %s\n' "$system_manager_node_output" >&2
    exit 1
  fi
fi

printf 'Process memory guard tests passed\n'
