#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

status=0

for route in '/api/options' '/api/options/yaml' '/api/options/yaml/location' 'logs/cache/bridge/config/bans/share-grant token' 'share-grant token/backfill' 'MusicBrainz subscription'; do
  if ! rg -n -F "$route" docs/security-bug-burndown.md >/dev/null; then
    printf 'compatibility no-op documentation check failed: expected inventory token missing: %s\n' "$route" >&2
    status=1
  fi
done

implementation_docs=(crates/slskr/src/lib.rs crates/slskr/src/controller_tests/*.rs docs/security-bug-burndown.md docs/http-api.md docs/app-surface.md "$ledger")

for expected in 'not active in this runtime' 'acknowledgement|acknowledged|persisted compatibility acknowledgement' 'compatibility_acknowledgement' 'compatibility_noop_routes_advertise_supported_shape' 'remote_options_overlay_and_yaml_are_effective_and_durable'; do
  if ! rg -n "$expected" "${implementation_docs[@]}" >/dev/null; then
    printf 'compatibility no-op documentation check failed: expected implementation/docs token missing: %s\n' "$expected" >&2
    status=1
  fi
done

if [[ "$status" -ne 0 ]]; then
  exit "$status"
fi

printf 'compatibility no-op documentation check passed\n'
