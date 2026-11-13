#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
helper="${repo_root}/scripts/configure-ubuntu-apt-mirrors.sh"
test_root="$(mktemp -d "${TMPDIR:-/tmp}/slskr-apt-mirrors.XXXXXX")"
trap 'rm -rf -- "$test_root"' EXIT

mirror_dir="${test_root}/apt"
mkdir -p "${mirror_dir}/sources.list.d"
source_list="${mirror_dir}/sources.list"
deb822_sources="${mirror_dir}/sources.list.d/ubuntu.sources"
touch \
  "${mirror_dir}/apt-mirrors-archive.txt" \
  "${mirror_dir}/apt-mirrors-security.txt" \
  "${mirror_dir}/apt-mirrors-ports.txt"

cat >"$source_list" <<'EOF'
deb https://azure.archive.ubuntu.com/ubuntu/ noble main restricted
deb https://us.archive.ubuntu.com/ubuntu noble-updates main restricted
deb https://security.ubuntu.com/ubuntu/ noble-security main restricted
deb https://ports.ubuntu.com/ubuntu-ports/ noble main
deb https://packages.microsoft.com/ubuntu/24.04/prod noble main
EOF

cat >"$deb822_sources" <<'EOF'
Types: deb
URIs: http://archive.ubuntu.com/ubuntu/
Suites: noble noble-updates noble-backports
Components: main universe
EOF

SLSKR_APT_MIRROR_DIR="$mirror_dir" SLSKR_APT_SOURCE_DIR="$mirror_dir" "$helper"

assert_contains() {
  local expected="$1"
  local path="$2"
  if ! grep -Fq -- "$expected" "$path"; then
    printf 'APT mirror regression failed: expected %s in %s\n' "$expected" "$path" >&2
    exit 1
  fi
}

assert_contains "mirror+file:${mirror_dir}/apt-mirrors-archive.txt" "$source_list"
assert_contains "mirror+file:${mirror_dir}/apt-mirrors-security.txt" "$source_list"
assert_contains "mirror+file:${mirror_dir}/apt-mirrors-ports.txt" "$source_list"
assert_contains "mirror+file:${mirror_dir}/apt-mirrors-archive.txt" "$deb822_sources"
assert_contains 'https://packages.microsoft.com/ubuntu/24.04/prod' "$source_list"

assert_contains $'https://archive.ubuntu.com/ubuntu/\tpriority:1' "${mirror_dir}/apt-mirrors-archive.txt"
assert_contains $'https://mirrors.kernel.org/ubuntu/\tpriority:2' "${mirror_dir}/apt-mirrors-archive.txt"
assert_contains $'https://security.ubuntu.com/ubuntu/\tpriority:1' "${mirror_dir}/apt-mirrors-security.txt"
assert_contains $'https://mirrors.kernel.org/ubuntu/\tpriority:2' "${mirror_dir}/apt-mirrors-security.txt"
assert_contains $'https://ports.ubuntu.com/ubuntu-ports/\tpriority:1' "${mirror_dir}/apt-mirrors-ports.txt"
assert_contains $'https://mirror.csclub.uwaterloo.ca/ubuntu-ports/\tpriority:2' "${mirror_dir}/apt-mirrors-ports.txt"

cp "$source_list" "${source_list}.before"
cp "$deb822_sources" "${deb822_sources}.before"
SLSKR_APT_MIRROR_DIR="$mirror_dir" SLSKR_APT_SOURCE_DIR="$mirror_dir" "$helper"
cmp -s "${source_list}.before" "$source_list"
cmp -s "${deb822_sources}.before" "$deb822_sources"

printf 'Ubuntu APT mirror fallback regression passed.\n'
