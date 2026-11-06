# slskR PR #204 W1483–W1502 application evidence

This packet records the exact-hash application of 15 cross-selected target changes in 8 locale catalogs. Every current-value SHA-256 preimage matched the candidate-free input; every post-write value matched the cross-selected target hash; catalog file and Git blob readbacks matched the focused catalog commit.

Catalog commit: 15a3cfffc8f800f2420847e7a98e1f2e94b33819, tree bad4a26bcbd81f9dccf3f779acaf05d2c1866313, parent a8c2b4cf5f771f8b574001239aa9217697097d6f. A separate evidence-only commit follows it. Prior selections and holds remain hash-only.

Run python3 verify_application.py from this directory. With access to the source repository, pass --repo PATH to verify the commit tree and live catalog values. No tests, builds, or CI were run.
