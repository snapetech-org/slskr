# Setup experience contract

Apply this to slskR's current first-use credential dialog, the existing
Web UI connection flow, the share settings, and its annotated TOML/config
guides. The Web UI already prompts for Soulseek credentials when no usable
credentials are configured and lets desktop users choose process memory, the
OS credential store, or a restricted local credential file. systemd and
external secret-manager credentials remain operator-managed.

## Product-specific flow

Keep the first interaction focused on connecting the Soulseek session. Explain
credential storage choices in terms of the current deployment and preserve
the existing explicit choice; never default to writing a password into a
general config or browser storage. After connection, let the operator search
and download immediately.

Offer share roots as a separate optional step in the existing Shares settings.
Ask whether the operator intends to share files, then ask for specific roots
only if yes. Show current share scan/status before offering a scan. Keep
`auto_connect` optional, and direct service deployments to their existing
TOML, environment, systemd credential, or secret-manager route. Expose
Lidarr, mesh, pods, listening, and other integrations through their current
settings and feature guides when the operator chooses them.

## Contract

- Extend the credential dialog and existing settings; do not introduce a
  second wizard state store.
- Treat credentials, shares, downloads, and service startup as different
  decisions with different owners and risks.
- Use only existing configured-status signals to skip known answers. Never
  show a saved secret or infer a share root from a download path.
- Keep downloads usable without requiring shares, Lidarr, or mesh features.
- Validate with the existing connection/status and share scan paths; preserve
  retryable form state while redacting secrets from errors and diagnostics.
- Keep local, systemd, container, and remote deployment instructions in their
  current context-specific guides.

The basic path is credentials → connected status → search/download. Sharing and
advanced network or media features remain optional extensions of that path.

## Implementation tasks

Extend the first-use dialog and the current Shares pane; keep service-mode
configuration in its existing files and deployment guides.

- [x] **R1 — P1: Explain credential persistence beside the existing selector.**
  In `web/src/components/App.jsx`, add context below the credential-store
  selector for Memory, OS credential store, and Local credential file, and
  point systemd users to the existing service configuration instructions.
  Keep the current server-provided writable-mode filter.
  **Done when:** the operator sees whether credentials survive a restart and
  where they are stored before pressing Connect; the plaintext nature of
  `file` is explicit; systemd remains read-only from the UI.

- [x] **R2 — P1: Make the empty Shares view clearly optional and configuration
  owned.** In `web/src/components/System/Shares/index.jsx`, add an empty-state
  explanation that indexed shares are separate from download availability,
  sharing is not required for search/download, and share roots are configured
  through the existing TOML/environment path documented in
  `docs/configuration.md` and `docs/features/shares-and-browse.md`. Keep
  the current scan, cancel, and status controls.
  **Done when:** an empty or not-yet-scanned table is not presented as a
  broken core setup, no download path is suggested as a share root, and the UI
  does not add a second share-root editor.

- [x] **R3 — P2: Keep first-use success scoped to the Soulseek session.**
  In `web/src/components/App.jsx`, make the success/connection state after
  credential submission lead directly back to normal search and transfer
  controls. Do not gate that state on shares, Lidarr, mesh, pods, or
  auto-connect configuration.
  **Done when:** a user can connect, search, and download with the current
  basic path while optional sharing and integrations remain untouched.
