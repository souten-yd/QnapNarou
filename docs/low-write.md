# QnapNarou — low disk I/O assessment (M4)

## Scope and safety

The production QTS wrapper suppresses persistent Web access logs and regularly scheduled release polling; the native narou.rs novel library and SQLite database are deliberately persistent. Existing SQLite journal_mode WAL and synchronous NORMAL are untouched. The read-only `io_probe.py` only reads `/proc/diskstats` on demand and prints JSON to stdout; it never writes to disk, changes configuration, or starts a background daemon. Use a temporary RAM-backed shell session and **do not redirect output onto an HDD**.

v0.1.11 builds the reviewed original narou.rs v0.5.3 and does **not** contain the older experimental M4 SQLite cache patch or novel-data write-behind optimization. No verified idle IOPS reduction is claimed. Built-in `NAROU_RS_DISABLE_SELF_UPDATE` and `PYTHONDONTWRITEBYTECODE` guards are part of v0.1.11.

## Measure on QTS 5.x

After QnapNarou v0.1.12 or later has been installed, inspect QPKG path via `/sbin/getcfg QnapNarou Install_Path -f /etc/config/qpkg.conf`, then run using the actual available Python 3 interpreter (for example `/opt/bin/python3.11`):

```sh
/opt/bin/python3.11 "$(/sbin/getcfg QnapNarou Install_Path -f /etc/config/qpkg.conf)/io_probe.py" --seconds 120 --disks sda sdb
```

Collect comparable idle samples with QnapNarou running, then stopped, and optionally with other known pollers stopped. Also check the same measurements during a real novel update (explicit workload), and after a NAS restart. Note RAID1 device counters may both reflect the same logical write. Report both read/write IOPS, MiB/s and busy %, and record baseline app version and whether indexing, QTS services, backups or Docker were active. Counters reflect **all** disk users and cannot identify an individual writing process.

## Deferred experiments

The original Draft PR #4 included an optional 16 MiB SQLite cache and temporary SQL objects in memory. It was based on an obsolete branch and cannot be merged onto main verbatim. Rebase and review against the pinned upstream v0.5.3; run native/QDK builds, SQLite WAL persistence, power-loss/rollback, repeated EPUB and downloaded-novel checks and actual QTS idle IOPS comparisons. Only then consider an explicitly reviewed, opt-in cache build. Never put SQLite database or WAL files in tmpfs without robust crash-safe replay and backups.

No automatic NAS updates, unbounded cache, writes on a timer, or data migrations are introduced by this diagnostic-only patch.
