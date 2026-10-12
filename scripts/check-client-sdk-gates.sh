#!/usr/bin/env bash
set -euo pipefail

# SDK checks can install/build Go, Python, and Node dependencies. Bound the
# whole direct invocation rather than only individual package commands.
runner_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if ! "$runner_repo_root/scripts/process-memory-guard-active.sh"; then
  exec "$runner_repo_root/scripts/with-process-memory-guard.sh" "${BASH_SOURCE[0]}" "$@"
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
python_executable="${PYTHON_EXECUTABLE:-python3}"

if ! command -v "$python_executable" >/dev/null 2>&1; then
  printf '%s is not installed; cannot run client SDK tests.\n' "$python_executable" >&2
  exit 1
fi

section() {
  printf '\n==> %s\n' "$1"
}

run_go_tests() {
  section "Go client tests"
  count_go_test_events() {
    "$python_executable" -c '
import json
import sys

passed = 0
for line in sys.stdin:
    # systemd-run output pipes are not always reopenable as /dev/stderr.
    # Forward the stream through the inherited descriptor while counting it.
    sys.stderr.write(line)
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        continue
    if event.get("Action") == "pass" and event.get("Test"):
        passed += 1
if passed < 1:
    raise SystemExit("Go test output reported no passing test cases")
print(f"NATIVE_TESTS_PASSED={passed}")
'
  }

  if command -v go >/dev/null 2>&1; then
    (cd client-go && go test -json -mod=readonly ./... | count_go_test_events)
    return
  fi

  if command -v docker >/dev/null 2>&1; then
    docker run --rm \
      --user "$(id -u):$(id -g)" \
      -e GOCACHE=/tmp/go-build \
      -e GOMODCACHE=/tmp/go-mod \
      -v "$repo_root/client-go:/src" \
      -w /src \
      golang:1.23 \
      go test -json -mod=readonly ./... | count_go_test_events
    return
  fi

  printf 'go is not installed and docker fallback is unavailable; cannot run Go client tests.\n' >&2
  exit 1
}

run_python_checks() {
  section "Python client quality/test check"
  if git ls-files 'client-python/__pycache__/*' 'client-python/**/__pycache__/*' 'client-python/**/*.egg-info/*' 'client-python/*.egg-info/*' | grep -q .; then
    printf 'tracked Python build artifacts found under client-python; remove __pycache__ and egg-info outputs from git.\n' >&2
    exit 1
  fi

  local venv_dir
  venv_dir="$(mktemp -d)"
  local artifact_snapshot
  artifact_snapshot="$(mktemp)"
  find client-python \( -type d \( -name __pycache__ -o -name '*.egg-info' \) -o -type f -name '*.pyc' \) -print0 >"$artifact_snapshot"
  cleanup_python_artifacts() {
    rm -rf "$venv_dir"
    while IFS= read -r -d '' artifact; do
      if ! grep -Fzxq -- "$artifact" "$artifact_snapshot"; then
        rm -rf -- "$artifact"
      fi
    done < <(find client-python -depth \( -type d \( -name __pycache__ -o -name '*.egg-info' \) -o -type f -name '*.pyc' \) -print0)
    rm -f -- "$artifact_snapshot"
  }
  trap cleanup_python_artifacts RETURN

  "$python_executable" -m venv "$venv_dir"
  PIP_NO_CACHE_DIR=1 "$venv_dir/bin/python" -m pip install --upgrade pip >/dev/null
  PIP_NO_CACHE_DIR=1 "$venv_dir/bin/python" -m pip install -e "client-python[dev]" >/dev/null
  PYTHON_BIN="$venv_dir/bin/python" scripts/check-python-client-quality.sh

  PYTHONDONTWRITEBYTECODE=1 "$venv_dir/bin/python" -m compileall -q client-python
  "$venv_dir/bin/python" - <<'PY'
from slskr import BatchClient, SlskrClient, WebSocketClient

client = SlskrClient("http://localhost:8080", "test-token")
assert client.base_url == "http://localhost:8080"
assert BatchClient is not None
assert WebSocketClient is not None
PY
  "$venv_dir/bin/python" -m pytest -q --junitxml="$venv_dir/python-tests.xml" client-python/tests
  "$venv_dir/bin/python" - "$venv_dir/python-tests.xml" <<'PY'
import sys
import xml.etree.ElementTree as ET

root = ET.parse(sys.argv[1]).getroot()
cases = list(root.iter("testcase"))
passed = sum(not any(case.find(tag) is not None for tag in ("failure", "error", "skipped")) for case in cases)
if passed < 1:
    raise SystemExit("Python SDK test output reported no passing test cases")
print(f"NATIVE_TESTS_PASSED={passed}")
PY
  "$venv_dir/bin/python" -m pip check
  PYTHON_BIN="$venv_dir/bin/python" scripts/check-python-client-package.sh
}

run_typescript_checks() {
  section "TypeScript client lifecycle/build checks"
  if ! command -v npm >/dev/null 2>&1; then
    printf 'npm is not installed; cannot check TypeScript client.\n' >&2
    exit 1
  fi

  local ts_temp
  ts_temp="$(mktemp -d)"
  cleanup_typescript_report() {
    rm -rf -- "$ts_temp"
  }
  trap cleanup_typescript_report RETURN

  (
    cd client-ts
    if [[ ! -d node_modules ]]; then
      npm ci
    fi
    npm test -- --runInBand --json --outputFile="$ts_temp/typescript-tests.json"
    npm run lint
  )
  "$python_executable" - "$ts_temp/typescript-tests.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as report_file:
    report = json.load(report_file)
passed = report.get("numPassedTests", 0)
if not isinstance(passed, int) or passed < 1:
    raise SystemExit("TypeScript SDK test output reported no passing test cases")
print(f"NATIVE_TESTS_PASSED={passed}")
PY
  scripts/check-web-audit.sh client-ts
  # The package check builds once and verifies tracked dist before packing.
  scripts/check-typescript-client-package.sh
}

run_go_tests
run_python_checks
run_typescript_checks

printf '\nClient SDK gates passed.\n'
