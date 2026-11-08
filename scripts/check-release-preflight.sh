#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

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
