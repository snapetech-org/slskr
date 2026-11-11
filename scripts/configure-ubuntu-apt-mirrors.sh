#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -gt 0 ]]; then
  source_files=("$@")
else
  source_files=(
    /etc/apt/apt-mirrors*.txt
    /etc/apt/sources.list
    /etc/apt/sources.list.d/*.list
    /etc/apt/sources.list.d/*.sources
  )
fi

rewrite_command=(
  sed -E -i
  -e 's@https?://(azure\.archive|([a-z]{2}\.)?archive|security)\.ubuntu\.com/ubuntu/?@https://mirrors.kernel.org/ubuntu/@g'
  -e 's@https?://ports\.ubuntu\.com/ubuntu-ports/?@https://mirror.csclub.uwaterloo.ca/ubuntu-ports/@g'
)
for source_file in "${source_files[@]}"; do
  if [[ ! -f "$source_file" ]]; then
    continue
  fi
  if [[ -w "$source_file" ]]; then
    "${rewrite_command[@]}" "$source_file"
  else
    sudo "${rewrite_command[@]}" "$source_file"
  fi
done
