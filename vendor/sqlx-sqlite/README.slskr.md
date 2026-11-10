# Temporary SQLite security compatibility patch

This is the published `sqlx-sqlite` 0.9.0 crate, whose archive SHA-256 is
`488e99c397a62007e4229aec669a179816339afc6d2620ca6fa420dbee2e982c`.

Only the normalized manifest's `libsqlite3-sys` upper bound is changed, from
`<0.38.0` to `<0.40.0`. This carries the compatibility changes accepted upstream
in SQLx commits `94aafe3a68884d923b0798a767c8d7f6cfda89d2` and
`10462fa4414c6c7f1ed1d39bb31678e3b726878c`, without taking unrelated unreleased
SQLx changes. The application lockfile selects `libsqlite3-sys` 0.39.1, bundling
SQLite 3.54.1, to address RUSTSEC-2026-0459 / CVE-2026-119375.

The crate's unused lockfile is omitted. The archive's relative license-file
pointers are replaced with the full upstream licenses from the SQLx 0.9.0
release commit `75bc0487eb661da811bb7a3c5d158f1bd463fef4`. Runtime Rust source
is unchanged.

Remove this directory and its root `[patch.crates-io]` entry once a published
SQLx version permits the patched SQLite dependency. Regenerate the application
lockfile and rerun the security audit, workspace tests, and native platform CI.
