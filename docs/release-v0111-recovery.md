# v0.1.11 publication recovery (no native rebuild)

The [source build job](https://github.com/souten-yd/QnapNarou/actions/runs/40242801386) compiled pinned upstream narou.rs v0.5.3 and the original iOS/EPUB, QDK wrapper and icon patches. Rust build, EPUB regression, QDK packaging, and upload-artifact all passed. Its final **publication-only** step failed due to `(cd dist && sha256sum -c SHA256SUMS)`: the manifest uses filenames prefixed with `dist/`, so verification must occur at repository root.

- Native QPKG SHA-256: `282329935a7adcfe36c8dab68af2150b57f1867b79f5d1a38d9928ab52b777ea`.
- Source SHA `217f96c4b07c5b371bba634628f066d86d3554bc`; upstream SHA `4c0c15849690b12ee27faf617eabbb863b73d72a`.
- Original artifact ID `12617454693`, artifact ZIP SHA-256 `7b67bf0cbd31c6a6689461ac760ef3b730a93e9692d56996ca6a3263baa74fb5`; it expires 2026-11-08.

The one-shot publish-only recovery Action reuses that exact artifact, verifies original job-step success and pinned digests, then publishes v0.1.11 **on the original build commit**. It neither recompiles Rust nor touches QTS installation, downloaded novels, SQLite, or any new runtime default. It refuses a duplicate release. PR #18 diskstats probe is merged later and must ship only in a future QPKG, not be claimed as part of v0.1.11.

Hardware acceptance is still required before claiming production durability, idle-I/O improvement or reliable rollback.
