#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if [[ "$#" -eq 0 ]]; then
  printf 'usage: %s <command> [args...]\n' "${BASH_SOURCE[0]}" >&2
  exit 2
fi

hard_memory_kib=4194304
memory_kib="${SLSKR_PROCESS_MEMORY_MAX_KIB:-$hard_memory_kib}"
tasks_max="${SLSKR_PROCESS_TASKS_MAX:-512}"
host_platform="$(uname -s 2>/dev/null || printf 'unknown')"
virtual_memory_limit_supported=1
if [[ "$host_platform" == "Darwin" ]]; then
  # Darwin's shell does not expose a settable RLIMIT_AS through `ulimit -v`.
  # Keep Node's managed-heap cap and the process-guard nesting marker while
  # allowing macOS release artifacts to reach their compiler commands.
  virtual_memory_limit_supported=0
fi

if [[ ! "$memory_kib" =~ ^[1-9][0-9]{0,7}$ || "$memory_kib" -gt "$hard_memory_kib" ]]; then
  printf 'SLSKR_PROCESS_MEMORY_MAX_KIB must be between 1 and %s KiB\n' "$hard_memory_kib" >&2
  exit 2
fi
if [[ ! "$tasks_max" =~ ^[1-9][0-9]{0,5}$ || "$tasks_max" -gt 512 ]]; then
  printf 'SLSKR_PROCESS_TASKS_MAX must be between 1 and 512\n' >&2
  exit 2
fi

process_guard_context_active=0
if scripts/process-memory-guard-active.sh "$memory_kib"; then
  process_guard_context_active=1
fi

# Keep Node's managed heap below the process cap. Chromium's native mappings
# remain bounded by the cgroup or virtual-memory ceiling below.
case "$(basename "$1")" in
  node|nodejs|npm|npx|vite|vitest|playwright)
    if [[ "${NODE_OPTIONS:-}" != *--max-old-space-size=* ]]; then
      export NODE_OPTIONS="${NODE_OPTIONS:-} --max-old-space-size=1024"
    fi
    ;;
esac

# Reuse an inherited, verified boundary. Adding RLIMIT_AS inside a resident
# cgroup prevents V8/Chromium from reserving address space even though their
# real memory and swap remain bounded by the parent unit.
if [[ "$process_guard_context_active" -eq 1 ]]; then
  exec "$@"
fi

force_system_manager="${SLSKR_PROCESS_MEMORY_GUARD_FORCE_SYSTEM_MANAGER:-0}"
case "$force_system_manager" in
  0|1) ;;
  *)
    printf 'SLSKR_PROCESS_MEMORY_GUARD_FORCE_SYSTEM_MANAGER must be 0 or 1\n' >&2
    exit 2
    ;;
esac

systemd_manager=""
systemd_run_prefix=()
systemd_stop_prefix=()
if [[ "${SLSKR_PROCESS_MEMORY_GUARD_DISABLE_SYSTEMD:-0}" != "1" ]] \
  && [[ "$process_guard_context_active" -eq 0 ]] \
  && [[ "$host_platform" == "Linux" ]] \
  && command -v systemd-run >/dev/null 2>&1 \
  && command -v systemctl >/dev/null 2>&1; then
  if [[ "$force_system_manager" != "1" ]] \
    && systemctl --user show-environment >/dev/null 2>&1; then
    systemd_manager="user"
    systemd_run_prefix=(systemd-run --user)
    systemd_stop_prefix=(systemctl --user)
  elif [[ "$(id -u)" == "0" ]] \
    && systemctl show-environment >/dev/null 2>&1; then
    systemd_manager="system"
    systemd_run_prefix=(systemd-run)
    systemd_stop_prefix=(systemctl)
  elif command -v sudo >/dev/null 2>&1 \
    && sudo -n systemctl show-environment >/dev/null 2>&1; then
    # Hosted runners often have a system manager but no user manager. Keep the
    # same cgroup memory/swap bound without RLIMIT_AS, which constrains V8's
    # and Chromium's address-space reservations before their resident memory
    # reaches the configured ceiling.
    systemd_manager="system"
    systemd_run_prefix=(sudo -n systemd-run)
    systemd_stop_prefix=(sudo -n systemctl)
  fi
fi

if [[ -n "$systemd_manager" ]]; then
  unit_name="slskr-process-memory-guard-${BASHPID}-${RANDOM}.service"
  environment_file=""
  # shellcheck disable=SC2329 # Invoked by the EXIT/INT/TERM trap below.
  cleanup_unit() {
    local status="$?"
    trap - EXIT INT TERM
    "${systemd_stop_prefix[@]}" stop "$unit_name" >/dev/null 2>&1 || true
    if [[ -n "$environment_file" ]]; then
      rm -f -- "$environment_file"
    fi
    exit "$status"
  }
  trap cleanup_unit EXIT INT TERM
  environment_file="$(mktemp "${TMPDIR:-/tmp}/slskr-process-memory-guard-environment.XXXXXX")"
  chmod 600 "$environment_file"
  while IFS= read -r -d '' environment_entry; do
    case "$environment_entry" in
      SLSKR_PROCESS_MEMORY_GUARD_HELD=*)
        continue
        ;;
    esac
    environment_name="${environment_entry%%=*}"
    environment_value="${environment_entry#*=}"
    printf -v escaped_environment_value '%q' "$environment_value"
    printf '%s=%s\n' "$environment_name" "$escaped_environment_value" >> "$environment_file"
  done < <(env -0)

  systemd_run_arguments=(
    --wait
    --pipe
    --collect
    --unit="$unit_name"
    --working-directory="$repo_root"
    --property="MemoryMax=${memory_kib}K"
    --property="MemorySwapMax=0"
    --property="TasksMax=$tasks_max"
    --property="EnvironmentFile=$environment_file"
    --setenv=SLSKR_PROCESS_MEMORY_GUARD_HELD=1
    --setenv=SLSKR_PROCESS_MEMORY_GUARD_UNIT="$unit_name"
  )
  if [[ "$systemd_manager" == "system" ]]; then
    systemd_run_arguments+=(--uid="$(id -u)")
  fi
  "${systemd_run_prefix[@]}" "${systemd_run_arguments[@]}" "$@"
  exit "$?"
fi

# Portable fallback for environments without an accessible systemd manager
# (including Git Bash and minimal containers). A virtual-memory ceiling is
# fail-closed: a browser that cannot operate within it exits instead of growing
# unbounded.
(
  if [[ "$virtual_memory_limit_supported" -eq 1 ]]; then
    if ! ulimit -v "$memory_kib"; then
      printf '[process-memory-guard] unable to apply virtual-memory ceiling on %s\n' "$host_platform" >&2
      exit 1
    fi
  else
    printf '[process-memory-guard] virtual-memory ceiling unavailable on %s; retaining managed-heap cap\n' "$host_platform" >&2
  fi
  export SLSKR_PROCESS_MEMORY_GUARD_HELD=1
  exec "$@"
)
