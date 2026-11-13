#!/usr/bin/env bash
set -euo pipefail

mirror_dir="${SLSKR_APT_MIRROR_DIR:-/etc/apt}"
source_dir="${SLSKR_APT_SOURCE_DIR:-$mirror_dir}"

if [[ "$#" -gt 0 ]]; then
  source_files=("$@")
else
  source_files=(
    "${source_dir}"/apt-mirrors*.txt
    "${source_dir}/sources.list"
    "${source_dir}"/sources.list.d/*.list
    "${source_dir}"/sources.list.d/*.sources
  )
fi

if [[ ! -d "$mirror_dir" ]]; then
  if [[ -w "$(dirname "$mirror_dir")" ]]; then
    mkdir -p "$mirror_dir"
  else
    sudo mkdir -p "$mirror_dir"
  fi
fi

write_mirror_list() {
  local path="$1"
  local content="$2"
  if [[ -w "$mirror_dir" ]]; then
    printf '%s' "$content" > "$path"
  else
    printf '%s' "$content" | sudo tee "$path" >/dev/null
  fi
}

archive_uri="mirror+file:${mirror_dir}/apt-mirrors-archive.txt"
security_uri="mirror+file:${mirror_dir}/apt-mirrors-security.txt"
ports_uri="mirror+file:${mirror_dir}/apt-mirrors-ports.txt"
archive_list="${mirror_dir}/apt-mirrors-archive.txt"
security_list="${mirror_dir}/apt-mirrors-security.txt"
ports_list="${mirror_dir}/apt-mirrors-ports.txt"

# Prefer Ubuntu's canonical endpoints and fail over to a separately hosted
# mirror only when a requested file cannot be fetched from the first endpoint.
write_mirror_list "$archive_list" \
  $'https://archive.ubuntu.com/ubuntu/\tpriority:1\nhttps://mirrors.kernel.org/ubuntu/\tpriority:2\n'
write_mirror_list "$security_list" \
  $'https://security.ubuntu.com/ubuntu/\tpriority:1\nhttps://mirrors.kernel.org/ubuntu/\tpriority:2\n'
write_mirror_list "$ports_list" \
  $'https://ports.ubuntu.com/ubuntu-ports/\tpriority:1\nhttps://mirror.csclub.uwaterloo.ca/ubuntu-ports/\tpriority:2\n'

escape_sed_replacement() {
  printf '%s' "$1" | sed -e 's/[\\&@]/\\&/g'
}

rewrite_command=(
  sed -E -i
  -e "s@https?://(azure\\.archive|([a-z]{2}\\.)?archive)\\.ubuntu\\.com/ubuntu/?@$(escape_sed_replacement "$archive_uri")@g"
  -e "s@https?://security\\.ubuntu\\.com/ubuntu/?@$(escape_sed_replacement "$security_uri")@g"
  -e "s@https?://ports\\.ubuntu\\.com/ubuntu-ports/?@$(escape_sed_replacement "$ports_uri")@g"
)
for source_file in "${source_files[@]}"; do
  if [[ ! -f "$source_file" ]]; then
    continue
  fi
  case "$source_file" in
    "$archive_list"|"$security_list"|"$ports_list")
      continue
      ;;
  esac
  if [[ -w "$source_file" ]]; then
    "${rewrite_command[@]}" "$source_file"
  else
    sudo "${rewrite_command[@]}" "$source_file"
  fi
done
