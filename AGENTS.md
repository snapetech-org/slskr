# Agent instructions - slskR

## Communication style

These interaction rules are standard for all model interfaces using this repo, including Hermes, Codex CLI, Claude CLI, Kilo CLI, OpenCode, Cursor, and similar agents:

- Never praise questions or validate premises before answers.
- If the user is wrong, say so immediately and directly.
- Do not capitulate under pushback unless new evidence or a stronger argument is provided.
- Do not anchor on numbers or estimates provided by the user. Generate an independent assessment first, then compare.
- Use explicit confidence levels when making claims, recommendations, or estimates: high, moderate, low, or unknown.
- Do not add disclaimers.
- Do not give ethics lectures unless explicitly asked.
- Do not use "it is important to consider" style hedges.
- Surface negative conclusions and bad news directly.
- Optimize for accuracy, not approval.
- If you do not know, say so. Never fabricate.

## Project boundaries

- slskR is a standalone Rust Soulseek client with a daemon, CLI, HTTP API, and a React/Vite Web UI. The shipped browser UI is in web/; docs describing the Rust/WASM UI are migration notes, not proof that it is the deployed interface.
- Keep Soulseek network use conservative. Respect peer rate limits and bandwidth, preserve user control, and do not add aggressive automatic browsing, probing, or discovery without an explicit product decision.
- Use test fixtures for unit and integration tests. Live-network interop uses the controlled setup in docs/live-interop-test-matrix.md and is not implied by a local test pass.
- Preserve API and SDK compatibility. Check the API contract and client-library docs before changing HTTP routes, event streams, auth, or shared payloads.
- Keep credentials in the documented credential sources. Never place real credentials, account data, or operator configuration in fixtures, test output, release notes, or PRs.
- Treat upstream implementations as read-only reference unless the task explicitly includes an upstream contribution. Preserve their attribution in forked files.

## Required reading

- Start with docs/README.md for the maintained documentation map.
- Read docs/architecture.md and docs/app-surface.md for daemon, API, and Web UI changes.
- Read docs/development/validation-engine.md before selecting or reporting automated checks.
- Read docs/live-interop-test-matrix.md and docs/full-network-test-plan.md before proposing live Soulseek or cross-client verification.
- Read docs/dev/rust-dependency-hygiene.md before changing Rust dependencies.
- Read docs/release.md and release-notes/README.md before preparing a release or release-note fragment.

## GitHub target safety

Before a GitHub write, make sure origin resolves to snapetech/slskr. Pass --repo snapetech/slskr to GitHub CLI commands that support that flag. For gh api, use an explicit repos/snapetech/slskr/... endpoint or set GH_REPO=snapetech/slskr; gh api does not accept --repo. Run scripts/verify-github-target.sh when that script exists in the checked-out revision. If it is absent, verify the origin URL and repository with GitHub CLI before writing; if either check is ambiguous or does not identify snapetech/slskr, stop. Never use an upstream remote as a write target.

## Rust build and tooling

Use Cargo and the pinned Rust toolchain directly. The workspace config keeps the large daemon crate on one Cargo build job, disables unnecessary dev debug metadata, and uses 16 codegen units plus ThinLTO for release builds. Do not add shell wrappers, compiler shims, virtual-memory limits, or forced test-thread settings around Rust commands. Run scripts/check-rust-format.sh for the changed-file formatter check; it intentionally leaves the historical multi-megabyte controller source alone.

## Validation engine

The repository engine is the source of task inventory, scheduling, isolation, and result accounting. Follow docs/development/validation-engine.md and use its plan, focused-task, tests-only, or full-run entry points as appropriate.
- A plan records discovery and prerequisites; it does not mean tests ran.
- Report actual tasks, native test counts, skips, exclusions, blocked tasks, and unavailable prerequisites separately.
- Use the pinned toolchain and disposable task environments. Do not run tests against real Soulseek accounts, live libraries, or operator databases.
- A local or mocked pass does not prove the GitHub-hosted platform matrix or live network interoperability.

## Release-note contract

Do not let user-facing behavior, security changes, operational changes, or user-facing documentation changes reach a release without a new validated fragment under release-notes/. Fragments are append-only and must capture the audience, product area, required action (or none), and breaking-change status. Internal-only work must be explicitly marked in the pull request. Preview the range with python3 scripts/release_notes.py preview --base <base> --head <head>.

## Release and publication

Use the release guide and current repository gates before preparing a release. Do not create tags, publish packages, or announce a release without explicit maintainer authorization.
