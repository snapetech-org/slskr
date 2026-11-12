#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"
export EIO_BACKEND="${SEMGREP_EIO_BACKEND:-posix}"
mode="all"
staged=0
ci_mode=0
while (($#)); do
  case "$1" in
    --staged) staged=1 ;;
    --semgrep-only)
      [[ "$mode" == all || "$mode" == semgrep ]] || { echo "Choose only one scanner." >&2; exit 2; }
      mode=semgrep ;;
    --trivy-only)
      [[ "$mode" == all || "$mode" == trivy ]] || { echo "Choose only one scanner." >&2; exit 2; }
      mode=trivy ;;
    --ci) ci_mode=1 ;;
    -h|--help)
      cat <<'HELP'
Usage: scripts/security-scan-local.sh [--staged] [--semgrep-only|--trivy-only] [--ci]

Semgrep uses the local Community Edition engine with p/default and metrics off.
Trivy selects secret, dependency, and IaC scanners from files in this repository.
Findings are report-only by default. Set SEMGREP_FAIL_ON_FINDINGS=1 or
TRIVY_EXIT_CODE=1 to make findings fail the command. --ci disables repository-
controlled Trivy config and ignore files. --staged scans only staged Semgrep files.
HELP
      exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done
if (( staged )) && [[ "$mode" == trivy ]]; then
  echo "Trivy scans the checkout, not the staged index; omit --staged for Trivy." >&2
  exit 2
fi

has_semgrep_input() {
  python3 "$repo_root/scripts/security-scan-inputs.py" semgrep
}

semgrep_run() {
  local args=(scan --config "${SEMGREP_CONFIG:-p/default}" --metrics=off --jobs "${SEMGREP_JOBS:-2}")
  local targets=()
  if [[ "${SEMGREP_OFFLINE:-0}" == 1 ]]; then
    args+=(--disable-version-check)
  fi
  if [[ "${SEMGREP_FAIL_ON_FINDINGS:-0}" == 1 ]]; then
    args+=(--error)
  fi
  if (( staged )); then
    while IFS= read -r -d '' file; do
      case "$file" in
        *.py|*.js|*.jsx|*.ts|*.tsx|*.mjs|*.cjs|*.go|*.rs|*.java|*.kt|*.kts|*.cs|*.c|*.h|*.cc|*.cpp|*.hpp|*.php|*.rb|*.swift|*.sh|*.bash|*.zsh|*.ps1|*.sql|*.scala|*.ex|*.exs|*.tf|Dockerfile|Dockerfile.*|docker-compose*.yml|docker-compose*.yaml|compose*.yml|compose*.yaml|*.yml|*.yaml)
          targets+=("$file") ;;
      esac
    done < <(git diff --cached --name-only --diff-filter=ACMR -z)
    if ((${#targets[@]} == 0)); then
      echo "Semgrep: no staged source or configuration files; skipped."
      return 0
    fi
  else
    if has_semgrep_input; then
      :
    else
      local discovery_status=$?
      if (( discovery_status == 1 )); then
        echo "Semgrep: no supported source or configuration files in this repository; skipped."
        return 0
      fi
      echo "Semgrep: failed to discover scan inputs; refusing to skip." >&2
      return "$discovery_status"
    fi
    targets=(.)
  fi

  echo "Semgrep Community Edition: config=${SEMGREP_CONFIG:-p/default}, targets=${#targets[@]}"
  if [[ -n "${SEMGREP_BIN:-}" ]]; then
    [[ -x "$SEMGREP_BIN" ]] || { echo "SEMGREP_BIN is not executable: $SEMGREP_BIN" >&2; return 127; }
    "$SEMGREP_BIN" "${args[@]}" "${targets[@]}"
  elif command -v uvx >/dev/null 2>&1; then
    local uv_args=()
    [[ "${SEMGREP_OFFLINE:-0}" == 1 ]] && uv_args+=(--offline)
    uvx "${uv_args[@]}" --from semgrep semgrep "${args[@]}" "${targets[@]}"
  elif command -v semgrep >/dev/null 2>&1; then
    semgrep "${args[@]}" "${targets[@]}"
  elif command -v docker >/dev/null 2>&1; then
    local image="semgrep/semgrep:latest"
    if ! docker image inspect "$image" >/dev/null 2>&1; then
      [[ "${SEMGREP_OFFLINE:-0}" == 0 ]] || { echo "Semgrep image is not cached for offline mode." >&2; return 127; }
      docker pull "$image"
    fi
    docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -e "EIO_BACKEND=${SEMGREP_EIO_BACKEND:-posix}" \
      -v "$repo_root:/src:ro" -w /src "$image" semgrep "${args[@]}" "${targets[@]}"
  else
    echo "Semgrep is unavailable. Install uv, pipx, Semgrep, or Docker." >&2
    return 127
  fi
}

trivy_run() {
  local scanner_list
  if ! scanner_list="$(python3 "$repo_root/scripts/security-scan-inputs.py" trivy)"; then
    echo "Trivy: failed to discover scan inputs; refusing to skip." >&2
    return 2
  fi
  if [[ -z "$scanner_list" ]]; then
    echo "Trivy: no source, dependency, or deployment files; skipped."
    return 0
  fi
  local args=()
  args+=(fs --scanners "$scanner_list" --timeout "${TRIVY_TIMEOUT:-20m}" --severity 'HIGH,CRITICAL' --ignore-unfixed --exit-code "${TRIVY_EXIT_CODE:-0}")
  for dir in .git .local node_modules vendor target dist build coverage .venv; do args+=(--skip-dirs "$dir"); done
  if (( ci_mode )); then args+=(--config= --ignorefile= --secret-config=); fi
  if [[ "${TRIVY_OFFLINE:-0}" == 1 ]]; then args+=(--skip-db-update --skip-java-db-update --skip-check-update); fi

  echo "Trivy filesystem scan: scanners=$scanner_list"
  if command -v trivy >/dev/null 2>&1; then
    trivy "${args[@]}" .
  elif command -v docker >/dev/null 2>&1; then
    local image="aquasec/trivy:latest"
    local cache_dir="${TRIVY_CACHE_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/trivy}"
    mkdir -p "$cache_dir"
    if ! docker image inspect "$image" >/dev/null 2>&1; then
      [[ "${TRIVY_OFFLINE:-0}" == 0 ]] || { echo "Trivy image is not cached for offline mode." >&2; return 127; }
      docker pull "$image"
    fi
    docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -e TRIVY_CACHE_DIR=/cache \
      -v "$repo_root:/src:ro" -v "$cache_dir:/cache" -w /src "$image" "${args[@]}" .
  else
    echo "Trivy is unavailable; install Trivy or Docker to run this project scan." >&2
    [[ "${REQUIRE_TRIVY:-0}" == 1 ]] && return 127
  fi
}

if [[ "$mode" == all ]] && (( ! staged )) && [[ -x scripts/run-security-scans.sh ]]; then
  # Preserve this repository's established Semgrep + Trivy policy and exclusions.
  SLSKR_SECURITY_SCANS_REQUIRED="${SLSKR_SECURITY_SCANS_REQUIRED:-0}" bash scripts/run-security-scans.sh
  exit $?
fi
if [[ "$mode" != trivy ]]; then
  if (( staged )); then
    semgrep_run
  elif [[ -x scripts/semgrep-local.sh && -z "${SEMGREP_BIN:-}" && "${SEMGREP_USE_GENERIC:-0}" != 1 ]]; then
    bash scripts/semgrep-local.sh
  elif [[ -x scripts/security-scan.sh && -z "${SEMGREP_BIN:-}" && "${SEMGREP_USE_GENERIC:-0}" != 1 ]]; then
    bash scripts/security-scan.sh
  else
    semgrep_run
  fi
fi
if [[ "$mode" != semgrep ]] && (( ! staged )); then trivy_run; fi
