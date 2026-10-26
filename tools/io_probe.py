#!/usr/bin/env python3
"""One-shot read-only QTS disk activity sampling. No persistent output or daemon."""
import argparse
import json
import time
from pathlib import Path

DISKSTATS = Path("/proc/diskstats")
SECTOR_BYTES = 512

def parse_diskstats(value):
    result = {}
    for line in value.splitlines():
        fields = line.split()
        if len(fields) < 14:
            continue
        try:
            data = {
                "reads": int(fields[3]),
                "sectors_read": int(fields[5]),
                "writes": int(fields[7]),
                "sectors_written": int(fields[9]),
                "io_busy_ms": int(fields[12]),
            }
        except ValueError:
            continue
        if all(number >= 0 for number in data.values()):
            result[fields[2]] = data
    return result

def rates(before, after, seconds):
    if seconds <= 0:
        raise ValueError("elapsed time must be positive")
    out = {}
    for disk in before.keys() & after.keys():
        first, last = before[disk], after[disk]
        if any(last[key] < first[key] for key in first):
            continue  # Counter reset, device replacement, or irregular data
        out[disk] = {
            "read_iops": round((last["reads"] - first["reads"]) / seconds, 3),
            "write_iops": round((last["writes"] - first["writes"]) / seconds, 3),
            "read_mib_s": round((last["sectors_read"] - first["sectors_read"]) * SECTOR_BYTES / (1024 * 1024 * seconds), 4),
            "write_mib_s": round((last["sectors_written"] - first["sectors_written"]) * SECTOR_BYTES / (1024 * 1024 * seconds), 4),
            "busy_percent": round(min(100.0, 100.0 * (last["io_busy_ms"] - first["io_busy_ms"]) / (seconds * 1000)), 2),
        }
    return out

def read():
    return parse_diskstats(DISKSTATS.read_text(encoding="ascii"))

def main():
    p = argparse.ArgumentParser(description="QNAP diskstats sampler: all-process device counters, read-only")
    p.add_argument("--seconds", type=float, default=60.0)
    p.add_argument("--disks", nargs="+", default=["sda", "sdb"])
    args = p.parse_args()
    if not 5 <= args.seconds <= 3600:
        p.error("--seconds must be between 5 and 3600")
    if not args.disks or any(not d or "/" in d or len(d) > 64 for d in args.disks):
        p.error("invalid disk name; use names like sda sdb")
    start = time.monotonic()
    before = read()
    time.sleep(args.seconds)
    elapsed = time.monotonic() - start
    data = rates(before, read(), elapsed)
    chosen = {name: data[name] for name in args.disks if name in data}
    print(json.dumps({
        "elapsed_seconds": round(elapsed, 2),
        "disks": chosen,
        "missing_disks": [name for name in args.disks if name not in data],
        "warning": "Linux device-wide counters (including other processes and RAID); not attributable to QnapNarou alone",
    }, ensure_ascii=False, indent=2))
    return 0 if chosen else 1

if __name__ == "__main__":
    raise SystemExit(main())
