# Security scanning

Run `./scripts/security-scan-local.sh` to scan this checkout locally. Semgrep Community Edition uses the free `p/default` community rules with metrics disabled; the source stays on the machine. The rule pack is fetched from the public Semgrep Registry when it is missing or refreshed, so the first scan needs network access. For a disconnected run, set `SEMGREP_CONFIG` to a local rules directory and `SEMGREP_OFFLINE=1` after caching the Semgrep package.

Semgrep runs on supported source and security configuration. It defaults to two worker jobs for memory-limited environments; set `SEMGREP_JOBS` to change that. Trivy selects `secret` for source/config, `vuln` when dependency manifests or lockfiles are present, and `misconfig` for container, workflow, Kubernetes, Helm, or Terraform files.

The scanner discovers inputs from Git's tracked and non-ignored file list, so scan selection does not depend on optional tools being installed. Trivy skips local `.local` task evidence along with build outputs and dependency-install directories; those files are not part of the repository's release surface.

The installed pre-commit hook runs Semgrep on staged source/config files; Trivy runs during full local scans and any configured CI workflow.

An existing Semgrep workflow remains in place; this local setup supplements it.

An existing Trivy filesystem or local scan remains in place; this local wrapper does not replace it.

Scans report findings without failing by default so existing findings can be triaged. Set `SEMGREP_FAIL_ON_FINDINGS=1` or `TRIVY_EXIT_CODE=1` to make a local scan fail on findings. Trivy downloads its vulnerability and check databases automatically; use `TRIVY_OFFLINE=1` only after those databases are cached. The default timeout is 20 minutes for slow first downloads; set `TRIVY_TIMEOUT` to change it.

Run `./scripts/update-security-tools.sh` to refresh the local Semgrep package cache, pull the current Semgrep fallback image, and refresh Trivy's database. The standalone Semgrep and Trivy workflows are manually dispatched on `main`; the release gate also runs the pinned scanner images in required mode.

Semgrep uses the POSIX I/O backend by default for compatibility with restricted Linux runners. Set `SEMGREP_EIO_BACKEND` only if your runner needs a different backend.
