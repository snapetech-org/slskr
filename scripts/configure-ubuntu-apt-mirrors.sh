#!/usr/bin/env bash
set -euo pipefail

mirror_file="${1:-/etc/apt/apt-mirrors.txt}"
if [[ ! -f "$mirror_file" ]]; then
  exit 0
fi

if [[ -w "$mirror_file" ]]; then
  sed -i 's|azure\.archive\.ubuntu\.com|archive.ubuntu.com|g' "$mirror_file"
else
  sudo sed -i 's|azure\.archive\.ubuntu\.com|archive.ubuntu.com|g' "$mirror_file"
fi
