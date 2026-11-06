#!/usr/bin/env bash
set -euo pipefail

asset_dir="${1:?usage: check-linux-package-compatibility.sh <archive-directory>}"
archive="$(find "$asset_dir" -maxdepth 1 -name '*-x86_64-unknown-linux-musl.tar.gz' -print -quit)"
[[ -n "$archive" ]] || { echo 'Missing static Linux x64 archive.' >&2; exit 1; }
work_dir="$(mktemp -d "${RUNNER_TEMP:-${TMPDIR:-/tmp}}/slskr-linux-compat.XXXXXX")"
trap 'rm -rf -- "$work_dir"' EXIT

tar -xzf "$archive" --strip-components=1 -C "$work_dir"
if readelf -l "$work_dir/slskr" | grep -q 'INTERP'; then
  echo 'The portable package binary requires a dynamic interpreter.' >&2
  exit 1
fi
for image in ubuntu:22.04 debian:bookworm-slim; do
  docker pull "$image"
  docker run --rm --network none \
    --volume "$work_dir:/release:ro" \
    --entrypoint /release/slskr "$image" version
done
