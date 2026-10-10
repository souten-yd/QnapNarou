# M2 local QDK build (x86_64 initial target)

M2 is an early, unvalidated packaging candidate. It is NOT yet ready to deploy.
Build upstream narou.rs on a libc-compatible target, and stage its complete `narou/` directory.

```sh
python3 tools/stage_release.py --source /path/to/narou --dest build/runtime
python3 tools/build_qdk.py --runtime build/runtime --out build/qdk --build
python3 -m unittest discover -s tests -v
```

`--build` requires QDK's `qbuild`; omit it to inspect the file tree without QDK. x86_64 only until an ARM64 binary and corresponding QDK arch payload exist.

Web defaults to the upstream loopback bind and upstream security guard; external LAN access must be explicitly configured in the narou.rs global settings. Do not bypass Basic authentication just to allow LAN access. Upstream Web UI remains unchanged.

Service data is in the sibling directory `QnapNarou-data`, not in the package folder, to avoid overwrite during package replacement. QTS exact path persistence, upgrade behavior, executable dependencies, qpkg.cfg metadata, App Center launch and shutdown behavior must be validated on an actual NAS before release.

Memory-write optimization is not yet implemented: the upstream runtime may write SQLite/WAL, configuration, downloads and logs normally. Avoid claiming that HDD access is reduced until M4 measurements.
