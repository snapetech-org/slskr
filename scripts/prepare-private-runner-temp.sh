#!/usr/bin/env bash
set -euo pipefail

fail() {
  printf '%s\n' "$1" >&2
  exit 1
}

validate_private_directory_chain() {
  local directory="$1"
  local runner_temp="$2"
  local current="$directory"
  local mode owner permissions sticky writable

  while :; do
    mode="$(stat -c '%a' -- "$current")" || fail "Could not determine permissions for $current."
    owner="$(stat -c '%u' -- "$current")" || fail "Could not determine owner for $current."
    [[ "$mode" =~ ^[0-7]{3,4}$ ]] || fail "Could not determine permissions for $current."
    permissions=$((8#$mode))
    sticky=$((permissions & 01000))
    writable=$((permissions & 0022))

    if [[ "$current" == "$runner_temp" ]]; then
      if [[ "$mode" != 700 ]]; then
        chmod 700 -- "$current" || fail 'Could not make RUNNER_TEMP private.'
        mode="$(stat -c '%a' -- "$current")" || fail 'Could not verify RUNNER_TEMP permissions.'
        [[ "$mode" == 700 ]] || fail 'RUNNER_TEMP must have mode 0700.'
      fi
    elif (( writable != 0 && sticky == 0 )); then
      fail "A RUNNER_TEMP parent directory is writable by other users without the sticky bit: $current"
    elif (( writable != 0 && sticky != 0 )) && [[ "$owner" != 0 && ! -O "$current" ]]; then
      fail "A writable sticky RUNNER_TEMP parent must be owned by root or the workflow runner: $current"
    fi

    [[ "$current" == / ]] && break
    current="$(dirname -- "$current")"
  done
}

validate_action_file() {
  local path="$1"
  local label="$2"
  local parent mode links current

  [[ -n "$path" && "$path" == /* && "$path" != *$'\n'* && "$path" != *$'\r'* ]] \
    || fail "$label must be an absolute path without line breaks."
  [[ -f "$path" && ! -L "$path" && -O "$path" ]] \
    || fail "$label must be a regular file owned by the workflow runner."
  links="$(stat -c '%h' -- "$path")" || fail "Could not inspect $label."
  [[ "$links" == 1 ]] || fail "$label must not have additional hard links."
  parent="$(cd -- "$(dirname -- "$path")" && pwd -P)" || fail "Could not resolve the $label directory."
  case "$parent" in
    "$runner_temp_resolved"|"$runner_temp_resolved"/*) ;;
    *) fail "$label must be inside RUNNER_TEMP." ;;
  esac
  current="$parent"
  while [[ "$current" != "$runner_temp_resolved" ]]; do
    case "$current" in
      "$runner_temp_resolved"/*) ;;
      *) fail "$label parent escaped RUNNER_TEMP." ;;
    esac
    [[ -d "$current" && ! -L "$current" && -O "$current" ]] \
      || fail "$label parent must be a directory owned by the workflow runner."
    chmod 700 -- "$current" || fail "Could not make the $label parent private."
    mode="$(stat -c '%a' -- "$current")" || fail "Could not verify the $label parent permissions."
    [[ "$mode" == 700 ]] || fail "$label parent must have mode 0700."
    current="$(dirname -- "$current")"
  done
  validate_private_directory_chain "$parent" "$runner_temp_resolved"
  chmod 600 -- "$path" || fail "Could not make $label private."
  mode="$(stat -c '%a' -- "$path")" || fail "Could not verify $label permissions."
  [[ "$mode" == 600 ]] || fail "$label must have mode 0600."
}

[[ -v RUNNER_TEMP ]] || fail 'RUNNER_TEMP is required.'
if [[ -z "$RUNNER_TEMP" || "$RUNNER_TEMP" != /* || "$RUNNER_TEMP" == *$'\n'* || "$RUNNER_TEMP" == *$'\r'* || ! -d "$RUNNER_TEMP" || ! -r "$RUNNER_TEMP" || ! -w "$RUNNER_TEMP" || ! -x "$RUNNER_TEMP" ]]; then
  fail 'RUNNER_TEMP must be an absolute, readable, writable directory without line breaks.'
fi

runner_temp_resolved="$(cd -- "$RUNNER_TEMP" && pwd -P)" || fail 'Could not resolve RUNNER_TEMP.'
if [[ "$runner_temp_resolved" == *$'\n'* || "$runner_temp_resolved" == *$'\r'* ]]; then
  fail 'RUNNER_TEMP must not resolve to a path containing line breaks.'
fi
case "$runner_temp_resolved" in
  /|/tmp|/tmp/*|/var/tmp|/var/tmp/*|/dev/shm|/dev/shm/*)
    fail 'RUNNER_TEMP must not resolve to a shared or root temporary directory.'
    ;;
esac
[[ -O "$runner_temp_resolved" ]] || fail 'RUNNER_TEMP must be owned by the workflow runner user.'
validate_private_directory_chain "$runner_temp_resolved" "$runner_temp_resolved"

[[ -v PRIVATE_RUNNER_TEMP_PREFIX && -n "$PRIVATE_RUNNER_TEMP_PREFIX" && "$PRIVATE_RUNNER_TEMP_PREFIX" =~ ^[a-z0-9][a-z0-9-]{0,23}$ ]] \
  || fail 'PRIVATE_RUNNER_TEMP_PREFIX must be a short lowercase name.'
[[ -v GITHUB_ENV && -v GITHUB_OUTPUT && -n "$GITHUB_ENV" && -n "$GITHUB_OUTPUT" && "$GITHUB_ENV" != "$GITHUB_OUTPUT" ]] \
  || fail 'GITHUB_ENV and GITHUB_OUTPUT must be present and distinct.'
validate_action_file "$GITHUB_ENV" 'GITHUB_ENV'
validate_action_file "$GITHUB_OUTPUT" 'GITHUB_OUTPUT'
env_identity="$(stat -c '%d:%i' -- "$GITHUB_ENV")" || fail 'Could not inspect GITHUB_ENV.'
output_identity="$(stat -c '%d:%i' -- "$GITHUB_OUTPUT")" || fail 'Could not inspect GITHUB_OUTPUT.'
[[ "$env_identity" != "$output_identity" ]] || fail 'GITHUB_ENV and GITHUB_OUTPUT must refer to distinct files.'

umask 077
job_temp="$(mktemp -d -- "$runner_temp_resolved/$PRIVATE_RUNNER_TEMP_PREFIX-job.XXXXXX")" \
  || fail 'Could not create private job temporary storage.'
chmod 700 -- "$job_temp"
[[ -O "$job_temp" ]] || fail 'Private job temporary storage has the wrong owner.'
job_temp_mode="$(stat -c '%a' -- "$job_temp")" || fail 'Could not verify private job temporary storage.'
[[ "$job_temp_mode" == 700 ]] || fail 'Private job temporary storage must have mode 0700.'
job_temp_resolved="$(cd -- "$job_temp" && pwd -P)" || fail 'Could not resolve private job temporary storage.'
case "$job_temp_resolved" in
  "$runner_temp_resolved"/*) ;;
  *) fail 'Private job temporary storage escaped RUNNER_TEMP.' ;;
esac

printf 'PRIVATE_RUNNER_TEMP=%s\nTMPDIR=%s\nTMP=%s\nTEMP=%s\n' \
  "$job_temp_resolved" "$job_temp_resolved" "$job_temp_resolved" "$job_temp_resolved" >> "$GITHUB_ENV"
printf 'path=%s\n' "$job_temp_resolved" >> "$GITHUB_OUTPUT"
