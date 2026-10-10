# Low-write operation: actual policy and measurement

QnapNarou prioritizes idle disk silence and safe persistence:

- No periodic GitHub release polling. Updates are checked only when clicking **最新版を確認**.
- The QNAP management HTTP server does not persist access logs.
- Python bytecode generation is disabled; in-RAM job status lives at /dev/shm/QnapNarou.
- Upstream file logging is turned off on first installation (only once); never overwrite later user changes.
- Existing upstream SQLite uses WAL / synchronous NORMAL, so data writes still occur on committed novel updates and settings changes. This is intentional for crash safety.
- QPKG upgrade downloads two packages to persistent storage (current version for rollback and future version). This unavoidable disk activity occurs only on a user-requested update.
- Application/library directories remain on persistent storage and are not silently moved to volatile tmpfs.
- No autonomous scans or background downloads are scheduled by the QNAP wrapper.

## Measurements on the actual NAS

Measure twice, under otherwise similar workloads:

1. Running QnapNarou:
   `/opt/bin/python3.11 tools/io_probe.py --seconds 120 --disks sda sdb`
2. QnapNarou stopped:
   use the same read-only measurement.
3. Compare write IOPS, write MiB/s and Busy %.
4. Repeat once with any other poller (HomeHub, backup, Docker, etc.) stopped to isolate the culprit.

The probe prints to stdout only; **do not redirect output to a file on an HDD**.
Diskstats counts are device totals, not per-process attribution. RAID1 writes may be visible on both physical disks.

## Current limitations / no invented claims

The upstream narou.rs application retains its own SQLite and download write behavior.
Memory buffering of noncritical management status is present, but full library
RAM-first batching is NOT implemented. Moving SQLite WAL to volatile tmpfs
requires a crash-safe replay/backup design and tests; this must never be done
by simply changing a directory to /tmp. Do not claim a measured IOPS reduction
until an actual QTS on/off comparison has been recorded.

## Opt-in native memory cache build (M4)

The checked-in QNAP patch keeps SQLite temporary SQL objects in RAM and
uses a bounded 16 MiB SQLite page cache per connection. It does **not**
turn WAL or durable novel writes into volatile data. Build QNAP's patched
variant from a clean pinned checkout:

```sh
git submodule update --init --recursive
python3 tools/apply_qnap_patch.py
cd upstream/narou.rs
cargo local-build --locked --target x86_64-unknown-linux-musl
```

The QNAP service exports `NAROU_RS_QNAP_MEMORY_CACHE=1`. The environment
flag only takes effect when the source patch was explicitly applied before
the native compile. Failing `git apply --check` blocks release; never
silently omit the patch after upstream changes.

To return the upstream checkout to an unmodified tree, reverse **only this
known patch** after building:

```sh
git -C upstream/narou.rs apply -R ../../patches/sqlite-ram-cache.patch
```

This is a cache optimization, not the requested full write-behind library.
No verified IOPS reduction or measured data durability change is claimed.
