#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

pin_policy="docs/dev/github-actions-pin-policy.md"
status=0

for expected in \
  'ACTIONLINT_VERSION: v' \
  'SLSKR_SECURITY_SCANS_REQUIRED:' \
  'SLSKR_SEMGREP_IMAGE: semgrep/semgrep:' \
  'SLSKR_TRIVY_IMAGE: aquasec/trivy:' \
  'actions: read' \
  'concurrency:' \
  'actions/attest-build-provenance@v4' \
  'attestations: write' \
  'id-token: write'; do
  if ! rg -n -F -- "$expected" .github/workflows >/dev/null; then
    printf 'workflow release policy check failed: expected workflow hardening token missing: %s\n' "$expected" >&2
    status=1
  fi
done

push_branches="$(
  awk '
    /^  push:$/ { in_push=1; next }
    in_push && /^  [[:alpha:]_][[:alnum:]_-]*:/ { exit }
    in_push && /^    branches:$/ { in_branches=1; next }
    in_branches && /^    [[:alpha:]_][[:alnum:]_-]*:/ { exit }
    in_branches && /^      - / {
      branch=$0
      sub(/^      - /, "", branch)
      gsub(/["\047]/, "", branch)
      print branch
    }
  ' .github/workflows/ci.yml
)"
if [[ "$push_branches" != "main" ]]; then
  printf 'workflow release policy check failed: only main pushes may enter the CI workflow\n' >&2
  status=1
fi
approved_events='["push","workflow_dispatch","schedule","release","repository_dispatch"]'
event_gate="contains(fromJSON('$approved_events'), github.event_name)"
ref_gate="github.ref == 'refs/heads/main' || (github.ref_type == 'tag' && startsWith(github.ref_name, 'v'))"
for job in web-assets controller-regex-parity rust platform-builds package-surfaces; do
  job_block="$(sed -n "/^  $job:/,/^  [A-Za-z0-9_-]*:/p" .github/workflows/ci.yml)"
  if [[ "$job_block" != *"ng-shared-main-jit"* ||
        "$job_block" != *"ng-shared-main-slskr"* ||
        "$job_block" != *"ng-main-run-{0}"* ||
        "$job_block" != *"github.run_id"* ||
        "$job_block" != *"$event_gate"* ||
        "$job_block" != *"$ref_gate"* ||
        "$job_block" != *"github.run_attempt > 1"* ||
        "$job_block" != *"||"* ]]; then
    printf 'workflow release policy check failed: %s must route only trusted main work to the shared pool\n' "$job" >&2
    status=1
  fi
done
controller_parity_job="$(sed -n '/^  controller-regex-parity:/,/^  [A-Za-z0-9_-]*:/p' .github/workflows/ci.yml)"
if [[ "$controller_parity_job" != *'DOTNET_INSTALL_DIR: ${{ github.workspace }}/.dotnet'* ||
      "$controller_parity_job" != *"DOTNET_VERSION: '10.0.402'"* ||
      "$controller_parity_job" != *"actions/setup-dotnet@a98b56852c35b8e3190ac28c8c2271da59106c68"* ||
      "$controller_parity_job" != *'dotnet-version: ${{ env.DOTNET_VERSION }}'* ]]; then
  printf 'workflow release policy check failed: controller regex parity must install its pinned .NET SDK into the workspace\n' >&2
  status=1
fi
dotnet_setup_line="$(rg -n -m 1 -F 'uses: actions/setup-dotnet@' .github/workflows/ci.yml | cut -d: -f1 || true)"
dotnet_info_line="$(rg -n -m 1 -F 'name: Record .NET runtime used by the upstream references' .github/workflows/ci.yml | cut -d: -f1 || true)"
if [[ -z "$dotnet_setup_line" || -z "$dotnet_info_line" || "$dotnet_setup_line" -ge "$dotnet_info_line" ]]; then
  printf 'workflow release policy check failed: controller parity must install .NET before using dotnet\n' >&2
  status=1
fi
route_count="$(rg -n -F 'ng-shared-main-jit' .github/workflows/ci.yml | wc -l)"
if [[ "$route_count" -ne 5 ]]; then
  printf 'workflow release policy check failed: unexpected shared runner route count in CI\n' >&2
  status=1
fi
for workflow in codeql.yml semgrep-community.yml trivy-filesystem.yml; do
  workflow_path=".github/workflows/$workflow"
  if [[ ! -f "$workflow_path" ]] ||
     ! rg -n -F 'ng-shared-main-jit' "$workflow_path" >/dev/null ||
     ! rg -n -F 'ng-shared-main-slskr' "$workflow_path" >/dev/null ||
     ! rg -n -F 'ng-main-run-{0}' "$workflow_path" >/dev/null ||
     ! rg -n -F 'github.run_id' "$workflow_path" >/dev/null ||
     ! rg -n -F "github.event_name == 'push'" "$workflow_path" >/dev/null ||
     ! rg -n -F "github.event_name == 'workflow_dispatch'" "$workflow_path" >/dev/null ||
     ! rg -n -F "github.event_name == 'schedule'" "$workflow_path" >/dev/null ||
     ! rg -n -F "github.ref == 'refs/heads/main'" "$workflow_path" >/dev/null ||
     ! rg -n -F "|| 'ubuntu-latest'" "$workflow_path" >/dev/null; then
    printf 'workflow release policy check failed: %s must use the pool only for trusted main scans\n' "$workflow_path" >&2
    status=1
  fi
done
for workflow in .github/workflows/*.yml; do
  if ! rg -q -F 'ng-shared-main-jit' "$workflow"; then
    continue
  fi
  case "${workflow##*/}" in
    ci.yml|codeql.yml|semgrep-community.yml|trivy-filesystem.yml|release.yml|release-publish.yml) ;;
    *)
      printf 'workflow release policy check failed: unexpected shared runner route in %s\n' "$workflow" >&2
      status=1
      ;;
  esac
done
if [[ ! -f "$pin_policy" ]]; then
  printf 'workflow release policy check failed: GitHub Actions pin policy is missing: %s\n' "$pin_policy" >&2
  status=1
else
  while IFS= read -r line; do
    action="${line#*uses: }"
    action="${action%%#*}"
    action="${action%%[[:space:]]*}"

    if [[ "$action" == ./* || "$action" == docker://* ]]; then
      continue
    fi

    if [[ ! "$action" =~ @([0-9a-f]{40})$ ]]; then
      printf 'workflow release policy check failed: external action must be pinned to a 40-character commit SHA: %s\n' "$line" >&2
      status=1
      continue
    fi

    action_name="${action%@*}"
    action_sha="${action##*@}"
    if ! rg -n -F "| \`${action_name}\` |" "$pin_policy" >/dev/null; then
      printf 'workflow release policy check failed: pinned action is missing from policy ledger: %s\n' "$action_name" >&2
      status=1
    fi
    if ! rg -n -F "\`${action_sha}\`" "$pin_policy" >/dev/null; then
      printf 'workflow release policy check failed: pinned action SHA is missing from policy ledger: %s\n' "$action_sha" >&2
      status=1
    fi
  done < <(rg -n '^[[:space:]-]*uses:[[:space:]]+[^[:space:]#]+@[^[:space:]#]+' .github/workflows)
fi

codeql_workflow=".github/workflows/codeql.yml"
for expected in \
  'pull_request:' \
  'push:' \
  'schedule:' \
  'workflow_dispatch:' \
  'security-events: write' \
  'queries:' \
  '- uses: security-extended' \
  'language: actions' \
  'language: c-cpp' \
  'language: go' \
  'language: javascript-typescript' \
  'language: python' \
  'language: ruby' \
  'language: rust' \
  'build-mode: autobuild' \
  'build-mode: none' \
  'github/codeql-action/init@9b3254085494b55a0f7c4c2b3d2d52cc712ce370' \
  'github/codeql-action/analyze@9b3254085494b55a0f7c4c2b3d2d52cc712ce370'; do
  if ! rg -n -F -- "$expected" "$codeql_workflow" >/dev/null; then
    printf 'workflow release policy check failed: CodeQL coverage contract missing: %s\n' "$expected" >&2
    status=1
  fi
done

if ! rg -n -F 'scripts/run-security-scans.sh' .github/workflows scripts/run-release-gate.sh >/dev/null; then
  printf 'workflow release policy check failed: required security scan runner is not wired into CI/release gates\n' >&2
  status=1
fi

for expected in \
  'name: Live Parity' \
  'workflow_dispatch:' \
  'schedule:' \
  'node scripts/audit-rust-web-ui.mjs' \
  'scripts/run-slskd-api-compat-smoke.sh' \
  'SLSKR_SLSKD_API_SMOKE_DIR: target/slskd-api-smoke' \
  'SLSKR_SLSKD_API_SMOKE_TOKEN:' \
  'target/ux-audit/**' \
  'target/slskd-api-smoke/compatibility-summary.txt' \
  'Credentialed public live interop' \
  'SLSKR_LIVE_INTEROP_ENV: ${{ secrets.SLSKR_LIVE_INTEROP_ENV }}' \
  'cargo build --locked -p slskr' \
  'scripts/run-live-interop-matrix.sh' \
  'target/live-interop/*.tsv' \
  'credentialed-live-interop.tsv'; do
  if ! rg -n -F -- "$expected" .github/workflows/live-parity.yml >/dev/null; then
    printf 'workflow release policy check failed: live parity workflow token missing: %s\n' "$expected" >&2
    status=1
  fi
done

for expected in \
  '--all-udp-transports --cycles 3' \
  '--artifact target/reproducibility/shared-all-transports-shutdown.json' \
  '            target/reproducibility/shared-all-transports-shutdown.json'; do
  if ! rg -n -F -- "$expected" .github/workflows/ci.yml >/dev/null; then
    printf 'workflow release policy check failed: shared transport proof missing: %s\n' "$expected" >&2
    status=1
  fi
done

for expected in \
  'schedule:' \
  "cron: '43 8 * * *'" \
  'timeout-minutes: 25' \
  'python3 scripts/run-react-nightly-audit.py' \
  '--property=MemoryMax=4G --property=MemorySwapMax=0' \
  '--property=TasksMax=512 --property=RuntimeMaxSec=15min' \
  'target/react-nightly-audit/**' \
  'if-no-files-found: error' \
  'retention-days: 30'; do
  if ! rg -n -F -- "$expected" .github/workflows/react-nightly-audit.yml >/dev/null; then
    printf 'workflow release policy check failed: React nightly contract missing: %s\n' "$expected" >&2
    status=1
  fi
done

for expected in \
  'publish:' \
  'type: boolean' \
  'default: true' \
  'if: inputs.publish' \
  'timeout-minutes: 20' \
  'release-assets/chocolatey-validation.json' \
  'retention-days: 30'; do
  if ! rg -n -F -- "$expected" .github/workflows/publish-chocolatey.yml >/dev/null; then
    printf 'workflow release policy check failed: Chocolatey validation contract missing: %s\n' "$expected" >&2
    status=1
  fi
done

if rg -n -F 'path: target/live-interop/**' .github/workflows/live-parity.yml; then
  printf 'workflow release policy check failed: live parity artifacts must exclude the credential file\n' >&2
  status=1
fi

if rg -n 'go install "github.com/rhysd/actionlint/cmd/actionlint@latest"|go install github.com/rhysd/actionlint/cmd/actionlint@latest' .github/workflows; then
  printf 'workflow release policy check failed: actionlint install must stay pinned\n' >&2
  status=1
fi

for workflow in .github/workflows/ci.yml .github/workflows/release.yml; do
  if ! rg -n -F "go-version: '1.25.x'" "$workflow" >/dev/null; then
    printf 'workflow release policy check failed: actionlint v1.7.12 requires Go 1.25 or newer: %s\n' "$workflow" >&2
    status=1
  fi
done

if ! rg -n -F 'run: actionlint' .github/workflows/ci.yml >/dev/null; then
  printf 'workflow release policy check failed: installed actionlint must run in CI\n' >&2
  status=1
fi
for workflow in .github/workflows/ci.yml .github/workflows/windows-smoke.yml; do
  if ! rg -n -F 'run: ./scripts/select-windows-perl.ps1' "$workflow" >/dev/null; then
    printf 'workflow release policy check failed: shared Windows Perl selection missing: %s\n' "$workflow" >&2
    status=1
  fi
done
if ! rg -n -F 'Locale::Maketext::Simple' scripts/select-windows-perl.ps1 >/dev/null; then
  printf 'workflow release policy check failed: full Perl module validation missing\n' >&2
  status=1
fi

if ! rg -n -F "v*" .github/workflows/release.yml >/dev/null; then
  printf 'workflow release policy check failed: v tag trigger was not found\n' >&2
  status=1
fi

if rg -n -F "workflow_dispatch:" .github/workflows/release.yml >/dev/null; then
  printf 'workflow release policy check failed: release workflow must only run from v tags\n' >&2
  status=1
fi

if rg -n -F "types: [published]" .github/workflows/release-publish.yml >/dev/null; then
  printf 'workflow release policy check failed: downstream package publish must be dispatched after release assets are uploaded\n' >&2
  status=1
fi

if rg -n -F 'ref: main' .github/workflows/release-publish.yml >/dev/null; then
  printf 'workflow release policy check failed: downstream publishing must check out the selected release tag, not main\n' >&2
  status=1
fi

if ! rg -n -F 'ref: ${{ inputs.tag || github.event.inputs.tag || github.ref_name }}' .github/workflows/release-publish.yml >/dev/null; then
  printf 'workflow release policy check failed: downstream publishing tag checkout expression is missing\n' >&2
  status=1
fi

for expected in \
  'name: Checkout publisher logic pinned to this manual retry' \
  "if: github.event_name == 'workflow_dispatch'" \
  'ref: ${{ github.sha }}' \
  'name: Require main source for manual publisher retries' \
  'Manual publisher retries must run from main.'; do
  if ! rg -n -F -- "$expected" .github/workflows/release-publish.yml >/dev/null; then
    printf 'workflow release policy check failed: manual publisher logic must be pinned to the retry workflow commit: %s\n' "$expected" >&2
    status=1
  fi
done

for expected in \
  'workflow_call:' \
  'Build and push (ghcr)' \
  'platforms: linux/amd64,linux/arm64' \
  'push: true' \
  'Verify pushed GHCR manifest' \
  'scripts/run-container-shutdown-smoke.sh'; do
  if ! rg -n -F -- "$expected" .github/workflows/release-publish.yml >/dev/null; then
    printf 'workflow release policy check failed: container publishing contract token missing: %s\n' "$expected" >&2
    status=1
  fi
done

for expected in \
  'uses: ./.github/workflows/release-publish.yml' \
  'AUR_SSH_KEY: ${{ secrets.AUR_SSH_KEY }}' \
  'needs: [release]' \
  'packages: write'; do
  if ! rg -n -F -- "$expected" .github/workflows/release.yml >/dev/null; then
    printf 'workflow release policy check failed: release must call the downstream publisher: %s\n' "$expected" >&2
    status=1
  fi
done

for dockerfile in Dockerfile packaging/docker/release.Dockerfile; do
  for expected in 'STOPSIGNAL SIGTERM' 'ENTRYPOINT ["slskr"]' 'CMD ["serve"]'; do
    if ! rg -n -F -- "$expected" "$dockerfile" >/dev/null; then
      printf 'workflow release policy check failed: container lifecycle token missing from %s: %s\n' "$dockerfile" "$expected" >&2
      status=1
    fi
  done
done

for expected in \
  'push:' \
  'branches:' \
  '- main' \
  'cargo audit'; do
  if ! rg -n -F -- "$expected" .github/workflows/ci.yml >/dev/null; then
    printf 'workflow release policy check failed: CI must run advisory coverage on main pushes; missing token: %s\n' "$expected" >&2
    status=1
  fi
done

if ! python3 - .github/workflows/ci.yml <<'PYTHON'
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text()
group = next((line.strip() for line in text.splitlines() if line.strip().startswith("group:")), "")
cancel = next((line.strip() for line in text.splitlines() if line.strip().startswith("cancel-in-progress:")), "")
if not group.startswith("group: ng-ci-${{ github.workflow }}-${{ github.event_name }}-"):
    raise SystemExit("CI concurrency group must be scoped to this workflow and event")
if not group.endswith("-${{ github.run_attempt }}"):
    raise SystemExit("each CI run attempt must keep its own concurrency group")
if cancel != "cancel-in-progress: ${{ github.event_name == 'pull_request' || github.event_name == 'pull_request_target' }}":
    raise SystemExit("only superseded PR validation may be cancelled")
PYTHON
then
  printf 'workflow release policy check failed: CI concurrency must preserve main attempts and scope cancellation to superseded PR checks\n' >&2
  status=1
fi

for expected in \
  'scripts/submit-winget-release.ps1' \
  'WINGETCREATE_GITHUB_TOKEN'; do
  if ! rg -n -F -- "$expected" .github/workflows/release-publish.yml >/dev/null; then
    printf 'workflow release policy check failed: Winget submission token missing: %s\n' "$expected" >&2
    status=1
  fi
done

for expected in \
  'merge-upstream' \
  'git/refs/heads/' \
  'slskr-release-backup-' \
  'force = $true' \
  'wingetcreate submit'; do
  if ! rg -n -F -- "$expected" scripts/submit-winget-release.ps1 >/dev/null; then
    printf 'workflow release policy check failed: Winget fork recovery token missing: %s\n' "$expected" >&2
    status=1
  fi
done

if rg -n 'runs-on:[[:space:]]*\[self-hosted|packer-windows' .github/workflows .github/WINDOWS_RUNNER.md >/dev/null; then
  printf 'workflow release policy check failed: current Windows workflows/docs must not refer to retired self-hosted runners\n' >&2
  status=1
fi

if ! rg -n -F 'cargo audit' .github/workflows/ci.yml .github/workflows/release.yml scripts/run-release-gate.sh >/dev/null; then
  printf 'workflow release policy check failed: RustSec audit must stay wired into CI and release gates\n' >&2
  status=1
fi
for workflow in ci release; do
  workflow_path=".github/workflows/${workflow}.yml"
  for expected in \
    'CARGO_AUDIT_CACHE_SCHEMA: v2' \
    'key: cargo-audit-${{ env.CARGO_AUDIT_CACHE_SCHEMA }}-${{ runner.os }}-${{ runner.arch }}-${{ env.CARGO_AUDIT_VERSION }}' \
    'run: scripts/ensure-cargo-audit.sh' \
    'run: scripts/test-ensure-cargo-audit.sh'; do
    if ! rg -n -F -- "$expected" "$workflow_path" >/dev/null; then
      printf 'workflow release policy check failed: %s must keep cargo-audit cache/setup contract: %s\n' "$workflow_path" "$expected" >&2
      status=1
    fi
  done
done

for expected in \
  'tag_pattern=' \
  'v<semver>' \
  'Require Main CI' \
  'for _ in {1..240}' \
  '--workflow CI' \
  '--branch main' \
  '--commit "$RELEASE_SHA"' \
  'needs: [version, main-ci]' \
  "startsWith(github.ref, 'refs/tags/v')" \
  'version="$GITHUB_REF_NAME"' \
  'DISCORD_RELEASE_WEBHOOK_URL' \
  'Announce Discord Release' \
  'scripts/release_notes.py' \
  'User-facing changes' \
  'RELEASE_BODY' \
  'slskr Releases' \
  'scripts/validate-changelog.sh'; do
  if ! rg -n -F -- "$expected" .github/workflows/release.yml >/dev/null; then
    printf 'workflow release policy check failed: release tag policy token missing: %s\n' "$expected" >&2
    status=1
  fi
done

if ! rg -n -F 'v<semver>' docs/release.md >/dev/null; then
  printf 'workflow release policy check failed: release docs must document v<semver>\n' >&2
  status=1
fi

for expected in \
  'ref: ${{ inputs.tag }}' \
  'SHA256SUMS.txt' \
  'Get-FileHash' \
  'https://github.com/$env:GITHUB_REPOSITORY/releases/download/' \
  'Expand-Archive'; do
  if ! rg -n -F -- "$expected" .github/workflows/publish-chocolatey.yml >/dev/null; then
    printf 'workflow release policy check failed: Chocolatey release contract token missing: %s\n' "$expected" >&2
    status=1
  fi
done

if ! rg -n -F '`macos-15-intel`' docs/release.md >/dev/null; then
  printf 'workflow release policy check failed: release docs must document the current macOS Intel runner\n' >&2
  status=1
fi

if rg -n -F "'release-*'" .github/workflows/release.yml >/dev/null; then
  printf 'workflow release policy check failed: broad release-* tag trigger must not return\n' >&2
  status=1
fi

if [[ "$status" -ne 0 ]]; then
  exit "$status"
fi

printf 'workflow release policy check passed\n'
