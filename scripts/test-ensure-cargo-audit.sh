#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_root="$(mktemp -d "${TMPDIR:-/tmp}/slskr-cargo-audit.XXXXXXXX")"
trap 'rm -rf -- "$tmp_root"' EXIT

fake_bin="$tmp_root/fake-bin"
cargo_home="$tmp_root/cargo home"
github_path="$tmp_root/github-path"
install_marker="$tmp_root/install-marker"
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
    mkdir -p "${CARGO_HOME:?}/bin"
    cat > "${CARGO_HOME}/bin/cargo-audit" <<'FAKE_AUDIT'
#!/usr/bin/env bash
printf 'cargo-audit'
printf ' %s' "$@"
printf '\n'
FAKE_AUDIT
    chmod +x "${CARGO_HOME}/bin/cargo-audit"
    : > "${FAKE_CARGO_INSTALL_MARKER:?}"
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

cargo_output="$(
  CARGO_HOME="$cargo_home" \
  PATH="$cargo_home/bin:$fake_bin:$PATH" \
    cargo audit --version
)"
if [[ "$cargo_output" != 'cargo-audit audit --version' ]]; then
  printf 'cargo-audit setup test failed: Cargo could not resolve the cached subcommand: %s\n' "$cargo_output" >&2
  exit 1
fi

printf 'cargo-audit cache and PATH tests passed\n'
