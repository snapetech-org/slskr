#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "$0")/.." && pwd -P)"
helper="$repo_root/scripts/prepare-private-runner-temp.sh"
scratch_parent="$HOME"
scratch_parent="$(cd -- "$scratch_parent" && pwd -P)"
case "$scratch_parent" in
  /|/tmp|/tmp/*|/var/tmp|/var/tmp/*|/dev/shm|/dev/shm/*)
    scratch_parent="$PWD"
    ;;
esac
[[ -w "$scratch_parent" ]] || { printf 'No safe writable runner-temp test directory.\n' >&2; exit 1; }

scratch_root="$(mktemp -d -- "$scratch_parent/slskr-runner-temp-test.XXXXXX")"
runner_temp="$scratch_root/runner-temp"
github_command_directory="$runner_temp/_runner_file_commands"
github_env="$github_command_directory/github-env"
github_output="$github_command_directory/github-output"
private_temp=''
unsafe_link="$scratch_root/unsafe-runner-temp"
unsafe_parent="$scratch_root/unsafe-parent"
unsafe_temp="$unsafe_parent/runner-temp"
outside_env="$scratch_root/outside-env"
outside_output="$scratch_root/outside-output"

cleanup() {
  [[ -n "$private_temp" && -d "$private_temp" ]] && rmdir -- "$private_temp" 2>/dev/null || true
  [[ -L "$unsafe_link" ]] && unlink -- "$unsafe_link" 2>/dev/null || true
  [[ -f "$outside_env" ]] && unlink -- "$outside_env" 2>/dev/null || true
  [[ -f "$outside_output" ]] && unlink -- "$outside_output" 2>/dev/null || true
  [[ -f "$github_env" ]] && unlink -- "$github_env" 2>/dev/null || true
  [[ -f "$github_output" ]] && unlink -- "$github_output" 2>/dev/null || true
  [[ -d "$github_command_directory" ]] && rmdir -- "$github_command_directory" 2>/dev/null || true
  [[ -f "$unsafe_temp/github-env" ]] && unlink -- "$unsafe_temp/github-env" 2>/dev/null || true
  [[ -f "$unsafe_temp/github-output" ]] && unlink -- "$unsafe_temp/github-output" 2>/dev/null || true
  [[ -d "$unsafe_temp" ]] && rmdir -- "$unsafe_temp" 2>/dev/null || true
  [[ -d "$unsafe_parent" ]] && rmdir -- "$unsafe_parent" 2>/dev/null || true
  [[ -d "$private_temp" ]] && rmdir -- "$private_temp" 2>/dev/null || true
  [[ -d "$runner_temp" ]] && rmdir -- "$runner_temp" 2>/dev/null || true
  [[ -d "$scratch_root" ]] && rmdir -- "$scratch_root" 2>/dev/null || true
}
trap cleanup EXIT

mkdir -m 700 -- "$runner_temp"
chmod 775 -- "$runner_temp"
mkdir -m 775 -- "$github_command_directory"
: > "$github_env"
: > "$github_output"
chmod 600 -- "$github_env" "$github_output"

RUNNER_TEMP="$runner_temp" \
PRIVATE_RUNNER_TEMP_PREFIX=slskr \
GITHUB_ENV="$github_env" \
GITHUB_OUTPUT="$github_output" \
bash "$helper"

private_temp="$(sed -n 's/^path=//p' "$github_output")"
[[ -n "$private_temp" && -d "$private_temp" && ! -L "$private_temp" ]] \
  || { printf 'Private job directory was not exported safely.\n' >&2; exit 1; }
[[ "$private_temp" == "$runner_temp"/* ]] \
  || { printf 'Private job directory escaped RUNNER_TEMP.\n' >&2; exit 1; }
[[ "$(stat -c '%a' -- "$runner_temp")" == 700 ]] \
  || { printf 'Writable runner temp was not made private.\n' >&2; exit 1; }
[[ "$(stat -c '%a' -- "$github_command_directory")" == 700 ]] \
  || { printf 'Writable GitHub command-file directory was not made private.\n' >&2; exit 1; }
[[ "$(stat -c '%a' -- "$private_temp")" == 700 ]] \
  || { printf 'Private job directory is not mode 0700.\n' >&2; exit 1; }
[[ "$(stat -c '%a' -- "$github_env")" == 600 && "$(stat -c '%a' -- "$github_output")" == 600 ]] \
  || { printf 'GitHub command files are not private.\n' >&2; exit 1; }
for name in PRIVATE_RUNNER_TEMP TMPDIR TMP TEMP; do
  grep -Fxq "$name=$private_temp" "$github_env" \
    || { printf '%s was not pointed at the private job directory.\n' "$name" >&2; exit 1; }
done

mkdir -m 700 -- "$unsafe_parent"
chmod 775 -- "$unsafe_parent"
mkdir -m 700 -- "$unsafe_temp"
: > "$unsafe_temp/github-env"
: > "$unsafe_temp/github-output"
chmod 600 -- "$unsafe_temp/github-env" "$unsafe_temp/github-output"
if RUNNER_TEMP="$unsafe_temp" \
  PRIVATE_RUNNER_TEMP_PREFIX=slskr \
  GITHUB_ENV="$unsafe_temp/github-env" \
  GITHUB_OUTPUT="$unsafe_temp/github-output" \
  bash "$helper" >/dev/null 2>&1; then
  printf 'A non-sticky writable RUNNER_TEMP parent was accepted.\n' >&2
  exit 1
fi

: > "$outside_env"
: > "$outside_output"
chmod 600 -- "$outside_env" "$outside_output"
if RUNNER_TEMP="$runner_temp" \
  PRIVATE_RUNNER_TEMP_PREFIX=slskr \
  GITHUB_ENV="$outside_env" \
  GITHUB_OUTPUT="$outside_output" \
  bash "$helper" >/dev/null 2>&1; then
  printf 'GitHub command files outside RUNNER_TEMP were accepted.\n' >&2
  exit 1
fi

if RUNNER_TEMP=/tmp \
  PRIVATE_RUNNER_TEMP_PREFIX=slskr \
  GITHUB_ENV="$github_env" \
  GITHUB_OUTPUT="$github_output" \
  bash "$helper" >/dev/null 2>&1; then
  printf 'Shared /tmp was accepted as RUNNER_TEMP.\n' >&2
  exit 1
fi

ln -s /tmp "$unsafe_link"
if RUNNER_TEMP="$unsafe_link" \
  PRIVATE_RUNNER_TEMP_PREFIX=slskr \
  GITHUB_ENV="$github_env" \
  GITHUB_OUTPUT="$github_output" \
  bash "$helper" >/dev/null 2>&1; then
  printf 'A RUNNER_TEMP symlink to shared /tmp was accepted.\n' >&2
  exit 1
fi

if RUNNER_TEMP="$runner_temp" \
  PRIVATE_RUNNER_TEMP_PREFIX=../escape \
  GITHUB_ENV="$github_env" \
  GITHUB_OUTPUT="$github_output" \
  bash "$helper" >/dev/null 2>&1; then
  printf 'An unsafe private temp prefix was accepted.\n' >&2
  exit 1
fi

printf 'Private runner temp contract passed.\n'
