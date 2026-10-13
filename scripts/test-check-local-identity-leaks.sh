#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
scratch_root="$(mktemp -d "${TMPDIR:-/tmp}/slskr-identity-scan-test.XXXXXX")"
trap 'rm -rf -- "$scratch_root"' EXIT

mkdir -p "$scratch_root/repo/scripts" "$scratch_root/repo/docs" "$scratch_root/home"
cp "$repo_root/scripts/check-local-identity-leaks.sh" "$scratch_root/repo/scripts/"
git -C "$scratch_root/repo" init --quiet --initial-branch=main
git -C "$scratch_root/repo" config user.name 'Scanner Test'
git -C "$scratch_root/repo" config user.email 'scanner-test@example.invalid'
printf '## [Unreleased]\n\n' > "$scratch_root/repo/docs/CHANGELOG.md"
git -C "$scratch_root/repo" add docs/CHANGELOG.md
git -C "$scratch_root/repo" commit --quiet -m 'scanner test base'
git -C "$scratch_root/repo" tag release-v0.1.0

base_tree="$(git -C "$scratch_root/repo" rev-parse 'HEAD^{tree}')"
rewritten_before="$(git -C "$scratch_root/repo" commit-tree "$base_tree" -m 'unrelated old main history')"
sentinel='identity-scan-rewrite-sentinel-20261013'
git -C "$scratch_root/repo" commit --quiet --allow-empty -m "contains $sentinel"
head_sha="$(git -C "$scratch_root/repo" rev-parse HEAD)"
git -C "$scratch_root/repo" update-ref refs/remotes/origin/main "$head_sha"

if (
  cd "$scratch_root/repo"
  HOME="$scratch_root/home" \
  USER=workflow-runner \
  LOCAL_IDENTITY_DENYLIST="$sentinel" \
  LOCAL_IDENTITY_SCAN_COMMITS=1 \
  LOCAL_IDENTITY_SCAN_BASE_SHA="$rewritten_before" \
    bash scripts/check-local-identity-leaks.sh
) >"$scratch_root/output.log" 2>&1; then
  printf 'The scanner missed a commit after a rewritten main push.\n' >&2
  cat "$scratch_root/output.log" >&2
  exit 1
fi

if ! rg -Fq "recent commit messages: git log" "$scratch_root/output.log"; then
  printf 'The scanner did not inspect recent commit messages.\n' >&2
  cat "$scratch_root/output.log" >&2
  exit 1
fi
if ! rg -Fq 'recent commit messages: git log:1' "$scratch_root/output.log"; then
  printf 'The scanner did not report the sentinel commit message match.\n' >&2
  cat "$scratch_root/output.log" >&2
  exit 1
fi
printf 'Identity scanner detects commits after a rewritten main push.\n'
