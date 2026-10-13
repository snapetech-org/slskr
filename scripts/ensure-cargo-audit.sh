#!/usr/bin/env bash
set -euo pipefail

version="${CARGO_AUDIT_VERSION:-}"
if [[ -z "$version" ]]; then
  printf 'CARGO_AUDIT_VERSION must be set before preparing cargo-audit\n' >&2
  exit 1
fi
if [[ -z "${GITHUB_PATH:-}" ]]; then
  printf 'GITHUB_PATH must be set before preparing cargo-audit\n' >&2
  exit 1
fi

cargo_home="${CARGO_HOME:-$HOME/.cargo}"
cargo_bin_dir="$cargo_home/bin"
cargo_audit="$cargo_bin_dir/cargo-audit"
if [[ "$cargo_bin_dir" == *$'\n'* || "$cargo_bin_dir" == *$'\r'* ]]; then
  printf 'cargo-audit bin directory contains a line break\n' >&2
  exit 1
fi

expected_version="cargo-audit $version"
installed_version=""
if [[ -x "$cargo_audit" ]]; then
  installed_version="$("$cargo_audit" --version 2>/dev/null || true)"
fi

if [[ ! -x "$cargo_audit" ]]; then
  cargo install cargo-audit --version "$version" --locked
elif [[ "$installed_version" != "$expected_version" ]]; then
  cargo install cargo-audit --version "$version" --locked --force
fi

if [[ ! -x "$cargo_audit" ]]; then
  printf 'cargo-audit executable is missing after installation: %s\n' "$cargo_audit" >&2
  exit 1
fi

installed_version="$("$cargo_audit" --version 2>/dev/null || true)"
if [[ "$installed_version" != "$expected_version" ]]; then
  printf 'cargo-audit version mismatch: expected %s, got %s\n' "$expected_version" "${installed_version:-unavailable}" >&2
  exit 1
fi

printf '%s\n' "$cargo_bin_dir" >> "$GITHUB_PATH"
printf '%s\n' "$installed_version"
