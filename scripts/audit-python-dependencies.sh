#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

pip_audit_version="2.10.1"
if command -v uvx >/dev/null 2>&1; then
  pip_audit=(uvx --from "pip-audit==${pip_audit_version}" pip-audit)
else
  temporary_root="${RUNNER_TEMP:-${TMPDIR:-/tmp}}"
  tool_environment="$(mktemp -d "${temporary_root%/}/slskr-pip-audit.XXXXXXXX")"
  trap 'rm -rf -- "$tool_environment"' EXIT
  python3 -m venv "$tool_environment/venv"
  "$tool_environment/venv/bin/python" -m pip install \
    --disable-pip-version-check --no-input "pip-audit==${pip_audit_version}"
  pip_audit=("$tool_environment/venv/bin/pip-audit")
fi

for requirements in client-python/constraints.txt scripts/requirements-publication.txt; do
  printf '\n==> Auditing %s\n' "$requirements"
  "${pip_audit[@]}" --requirement "$requirements"
done
