## Runner policy — owner directive, 2026-11-03

Use compatible public GitHub-hosted runners by default, preserving each job's
required OS and architecture. Use private ephemeral JIT runners only when a
task requires private hardware, network, files, or other task-specific private
resources. Public pull-request code must run without secrets and with minimal
permissions; use disposable isolated execution when the task requires tighter
egress or environment controls. Preserve active builds and other agents' work.
Do not restart the broker while it owns running guests. Validate each workflow
revision on the runner class it selects; rerunning an old run uses its old
revision.

The shared JIT inventory lives in
`snapetech-org/packer/scripts/shared-jit-runner-pool/`. Check source routing,
runner-group access, deployed broker policy, and live capacity when a task
needs a private JIT route.

