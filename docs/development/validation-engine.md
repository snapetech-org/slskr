# Validation engine

The repository validation engine keeps SlskR's existing native test runners and
adds a source bound inventory, explicit task plan, execution receipt, and
same workflow attempt checks for the Rust platform test matrix.

## Local commands

```sh
node scripts/validate-development.mjs --plan --json
node scripts/validate-development.mjs --task rust-workspace-tests
node scripts/validate-development.mjs --tests-only
node scripts/validate-development.mjs
```

`--plan` is discovery only: it records the candidate, test file inventory,
available commands and selected tasks without running them. `--task` selects a
single registered task and its prerequisites. `--tests-only` runs the Rust
workspace tests, Go/Python/TypeScript SDK checks, repository Python tests, web
and dashboard Vitest suites, API lifecycle coverage, fixture Playwright tests,
and engine contract tests. The default command runs all registered local tasks,
including Rust formatting, Clippy, WASM, advisory, lint, typecheck, and build
checks.

Each execution receives a fresh private directory under the operating system's
temporary directory. Its receipt distinguishes planned, executed, passed,
failed, blocked, excluded, and active test cases. Logs are hashed and kept with
the receipt. Candidate identity includes the Git commit and tree, tracked diff,
untracked files, pinned input digests, and test inventory digests. The engine
checks this identity before and after every task and blocks later work if the
source changes during a run.

Runtime probes and child commands inherit only the executable path, platform
process variables, locale, timezone, and the Rust toolchain location. Each task
receives a run-owned home, temporary, and XDG configuration/cache directory.
Cargo uses a private cache shared only within that validation run. Registered task settings
remain task-scoped, and unapproved `passEnv` requests fail during planning.
`CI` is forced to `true`; Python user-site packages are disabled, and test tasks
use `NODE_ENV=test`.
Ambient credentials, loader options, proxy settings, workflow context, and
operator configuration paths are not inherited.

Rust cases are counted from Cargo's native test result summaries. The SDK gate
emits counts from Go JSON events, pytest JUnit output, and Jest JSON output.
Python unittest and Vitest/Playwright summaries are counted from their native
reports. Empty or missing test output cannot be reported as a pass.

During execution, the engine writes cumulative task progress to stderr at task
start and completion, with a heartbeat every minute for long tasks. It reports
completed, failed, blocked, and pending tasks plus the active task and elapsed
time. Native test-case totals update after each task finishes, since native
runner output may be buffered. In GitHub Actions these updates appear in the
live step log; the rendered job summary is published after the step completes.

Inventory globs are matched by bounded POSIX path segments (`*`, `?`, and
`**`). Test-content filtering, runtime versions, and native result summaries use
named engine matchers; repository configuration cannot provide executable
regular expressions for discovery or case accounting.

## GitHub test nodes

The required Rust workspace test runs are identified as `linux-x64`,
`linux-aarch64`, `macos-x64`, `macos-arm64`, and `windows-x64`. Each run exports
a short lived receipt containing the workflow run ID, attempt, source commit,
runner OS/architecture, test task, native case count, and inventory digests.
The reconciliation job rejects missing or duplicate runners, mismatched run or
attempt IDs, failed or empty test results, runner identity drift, and different
source or inventory snapshots. Package-surface checks depend on successful
reconciliation.

GitHub-hosted receipt collection is verified by GitHub Actions. A local run does
not establish hosted runner behavior. Existing release policy, static security,
package matrix, and reproducibility checks remain explicit workflow steps and
are not inferred from a local test receipt.
