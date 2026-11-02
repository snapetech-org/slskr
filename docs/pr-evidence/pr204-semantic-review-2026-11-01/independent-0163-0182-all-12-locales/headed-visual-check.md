# Headed visual review: exact-branch UI blocked by isolated-backend absence

A fresh, isolated headed Chrome session (no saved login) opened the exact catalog application at `http://192.168.50.148:53104/`. The front end was served from `2f7794cec0592ffd1a24490a5441b3ee7d1c728d` / tree `aa0c195ecf045fef9545ddbdc7df4a0da305943b`, the application commit containing all ten catalog changes.

The screenshot at 1440 × 900 and accessible page snapshot showed only the heading `Lost connection to slskR / Refresh to reconnect`. The app requested `/api/v0/session/enabled`; its isolated Vite proxy targeted unbound `127.0.0.1:55306` and returned connection-refused/502. I did not use the shared slskR daemon on port 5030. The Vite log also reported shared-cache icon fonts outside its serving allow list, but no app controls were available behind the connection overlay.

The exact blocker is a compatible source-built isolated backend. The cached standalone binary is stale and incompatible; compiling the current backend would violate the no-build boundary. The browser session and Vite server were closed, and only this task’s node_modules symlink, config, and 8 MiB Vite cache were removed. The screenshot showed only the connection error and was not retained. No tests, build, or CI were run.
