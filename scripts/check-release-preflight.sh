#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

for tool in rg git python3; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    printf 'Release preflight requires %s; install its tool prerequisites first.\n' "$tool" >&2
    exit 1
  fi
done

# Check source-only packaging rules before spending time on native compilation.
scripts/check-workflow-release-policy.sh
scripts/check-package-artifact-matrix.sh
scripts/check-aur-packaging-checksums.sh
scripts/check-release-version-metadata.sh
scripts/check-kubernetes-public-posture.sh
scripts/validate-changelog.sh
python3 scripts/test-release-metadata.py
python3 scripts/test-public-release.py
python3 scripts/test_release_notes.py
