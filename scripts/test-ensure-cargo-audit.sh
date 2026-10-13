#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_root="$(mktemp -d "${TMPDIR:-/tmp}/slskr-cargo-audit.XXXXXXXX")"
trap 'rm -rf -- "$tmp_root"' EXIT

fake_bin="$tmp_root/fake-bin"
cargo_home="$tmp_root/cargo home"
github_path="$tmp_root/github-path"
install_marker="$tmp_root/install-marker"
version_file="$cargo_home/fake-audit-version"
mkdir -p "$fake_bin" "$cargo_home"
: > "$github_path"

cat > "$fake_bin/cargo" <<'FAKE_CARGO'
#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
  install)
    if [[ "${2:-}" != "cargo-audit" ]]; then
      printf 'unexpected cargo install target: %s\n' "${2:-}" >&2
      exit 1
    fi
    if [[ -x "${CARGO_HOME:?}/bin/cargo-audit" && " $* " != *' --force '* ]]; then
      printf 'cargo install did not force-replace the existing cargo-audit executable\n' >&2
      exit 1
    fi
    if [[ "${3:-}" != "--version" || -z "${4:-}" ]]; then
      printf 'cargo install did not request a cargo-audit version\n' >&2
      exit 1
    fi
    version="$4"
    mkdir -p "${CARGO_HOME:?}/bin"
    cat > "${CARGO_HOME}/bin/cargo-audit" <<'FAKE_AUDIT'
#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == '--version' ]]; then
  printf 'cargo-audit %s\n' "$(cat "${CARGO_HOME:?}/fake-audit-version")"
else
  printf 'cargo-audit'
  printf ' %s' "$@"
  printf '\n'
fi
FAKE_AUDIT
    chmod +x "${CARGO_HOME}/bin/cargo-audit"
    printf '%s\n' "$version" > "${CARGO_HOME}/fake-audit-version"
    printf '%s\n' "$*" > "${FAKE_CARGO_INSTALL_MARKER:?}"
    ;;
  audit)
    shift
    exec cargo-audit audit "$@"
    ;;
  *)
    printf 'unexpected cargo command: %s\n' "${1:-}" >&2
    exit 1
    ;;
esac
FAKE_CARGO
chmod +x "$fake_bin/cargo"

CARGO_HOME="$cargo_home" \
CARGO_AUDIT_VERSION=0.22.1 \
GITHUB_PATH="$github_path" \
FAKE_CARGO_INSTALL_MARKER="$install_marker" \
PATH="$fake_bin:$PATH" \
  "$repo_root/scripts/ensure-cargo-audit.sh" > "$tmp_root/cache-miss.out"
if [[ ! -f "$install_marker" ]]; then
  printf 'cargo-audit setup test failed: cache-miss path did not install the tool\n' >&2
  exit 1
fi
if ! grep -Fx '0.22.1' "$version_file" >/dev/null; then
  printf 'cargo-audit setup test failed: cache-miss path installed the wrong version\n' >&2
  exit 1
fi
if ! grep -Fx "$cargo_home/bin" "$github_path" >/dev/null; then
  printf 'cargo-audit setup test failed: cargo bin directory was not added to GITHUB_PATH\n' >&2
  exit 1
fi

# A cache hit with cargo's bin directory absent from PATH must still be usable.
: > "$github_path"
rm -f -- "$install_marker"
CARGO_HOME="$cargo_home" \
CARGO_AUDIT_VERSION=0.22.1 \
GITHUB_PATH="$github_path" \
FAKE_CARGO_INSTALL_MARKER="$install_marker" \
PATH="$fake_bin:$PATH" \
  "$repo_root/scripts/ensure-cargo-audit.sh" > "$tmp_root/cache-hit.out"
if [[ -f "$install_marker" ]]; then
  printf 'cargo-audit setup test failed: cached tool was reinstalled\n' >&2
  exit 1
fi
if ! grep -Fx "$cargo_home/bin" "$github_path" >/dev/null; then
  printf 'cargo-audit setup test failed: cached bin directory was not added to GITHUB_PATH\n' >&2
  exit 1
fi

# A persistent runner can restore an executable from a stale cache key. The
# setup step must replace that binary with the requested version.
printf '0.21.0\n' > "$version_file"
: > "$github_path"
rm -f -- "$install_marker"
CARGO_HOME="$cargo_home" \
CARGO_AUDIT_VERSION=0.22.1 \
GITHUB_PATH="$github_path" \
FAKE_CARGO_INSTALL_MARKER="$install_marker" \
PATH="$fake_bin:$PATH" \
  "$repo_root/scripts/ensure-cargo-audit.sh" > "$tmp_root/stale-cache.out"
if [[ ! -f "$install_marker" ]] || ! grep -F -- '--force' "$install_marker" >/dev/null; then
  printf 'cargo-audit setup test failed: stale cached tool was not force-reinstalled\n' >&2
  exit 1
fi
if ! grep -Fx '0.22.1' "$version_file" >/dev/null; then
  printf 'cargo-audit setup test failed: stale cached tool was not replaced with the requested version\n' >&2
  exit 1
fi
if ! grep -Fx "$cargo_home/bin" "$github_path" >/dev/null; then
  printf 'cargo-audit setup test failed: stale cached bin directory was not added to GITHUB_PATH\n' >&2
  exit 1
fi

cargo_output="$(
  CARGO_HOME="$cargo_home" \
  PATH="$cargo_home/bin:$fake_bin:$PATH" \
    cargo audit --version
)"
if [[ "$cargo_output" != 'cargo-audit audit --version' ]]; then
  printf 'cargo-audit setup test failed: Cargo could not resolve the cached subcommand: %s\n' "$cargo_output" >&2
  exit 1
fi

printf 'cargo-audit version, cache, and PATH tests passed\n'
