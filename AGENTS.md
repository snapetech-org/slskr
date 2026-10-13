# Agent instructions - slskR

## Communication style

These interaction rules are standard for all model interfaces used with this repo, including Hermes, Codex CLI, Claude CLI, Kilo CLI, OpenCode, Cursor, and similar agents:

- Never praise questions or validate premises before answers.
- If the user is wrong, say so immediately and directly.
- Do not capitulate under pushback unless new evidence or a stronger argument is provided.
- Do not anchor on numbers or estimates provided by the user. Generate an independent assessment first, then compare.
- Use explicit confidence levels when making claims, recommendations, or estimates: `high`, `moderate`, `low`, or `unknown`.
- Do not add disclaimers.
- Do not give ethics lectures unless explicitly asked.
- Do not use "it is important to consider" style hedges.
- Surface negative conclusions and bad news directly.
- Optimize for accuracy, not approval.
- If you do not know, say so. Never fabricate.

## Machine inventory and scratch space

- `kspld0` is the desktop; `kspls0` is the server.
- Verified on 2026-10-12: `kspls0` stores its LVM data pool at
  `/mnt/datapool_lvm_media` (`/dev/mapper/datapool_lvm-media`, ext4). The same
  path is mounted on `kspld0` from `kspls0:/mnt/datapool_lvm_media` over
  NFSv4.2. Both hosts reported about 31 TiB available at verification time;
  free space changes, so check it again before each task.
- Before writing scratch data, confirm the target with `hostname`, then run
  `findmnt -T /mnt/datapool_lvm_media` and `df -hT
  /mnt/datapool_lvm_media` on that host. Do not assume the mount path or free
  capacity. Use a per-task directory and remove only files created for that
  task; preserve existing or ambiguous files.

## Release-note contract

Do not let user-facing behavior, security changes, operational changes, or
user-facing documentation changes reach a release without a new validated
fragment under `release-notes/`. Fragments are append-only and must capture the
audience, product area, required action (or `none`), and breaking-change status.
Internal-only work must be explicitly marked in the pull request. Preview the
range with `python3 scripts/release_notes.py preview --base <base> --head <head>`.

## Rust build and tooling

Use Cargo and the pinned Rust toolchain directly. The workspace config keeps
the large daemon crate on one Cargo build job, disables unnecessary dev debug
metadata, and uses 16 codegen units plus ThinLTO for release builds. Do not add
shell wrappers, compiler shims, virtual-memory limits, or forced test-thread
settings around Rust commands. Run `scripts/check-rust-format.sh` for the
changed-file formatter check; it intentionally leaves the historical
multi-megabyte controller source alone.
