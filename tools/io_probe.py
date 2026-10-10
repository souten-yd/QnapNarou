#!/usr/bin/env python3
"""Read-only QTS disk activity probe; writes nothing to persistent storage.

Run once with the service on, once stopped, then compare. /proc/diskstats
counts reflect ALL processes on a device, not only QnapNarou.
"""
import argparse
import json
import time
from pathlib import Path

DISKSTATS = Path("/proc/diskstats")
SECTOR_BYTES = 512


def parse_diskstats(text):
    result = {}
    for line in text.splitlines():
        fields = line.split()
        if len(fields) < 14:
            continue
        try:
            result[fields[2]] = {
                "writes": int(fields[7]),
                "sectors_written": int(fields[9]),
                "io_busy_ms": int(fields[12]),
            }
        except ValueError:
            continue
    return result


def rates(before, after, seconds):
    if seconds <= 0:
        raise ValueError("elapsed time must be positive")
    output = {}
    for disk in before.keys() & after.keys():
        first, last = before[disk], after[disk]
        if any(last[k] < first[k] for k in first):
            continue  # a counter reset or device replacement
        output[disk] = {
            "write_iops": round((last["writes"] - first["writes"]) / seconds, 3),
            "write_mib_s": round((last["sectors_written"] - first["sectors_written"]) *
                                 SECTOR_BYTES / (1024 * 1024 * seconds), 4),
            "busy_percent": round(min(100.0, 100 * (last["io_busy_ms"] -
                                                    first["io_busy_ms"]) / (seconds * 1000)), 2),
        }
    return output


def read():
    return parse_diskstats(DISKSTATS.read_text())


def main():
    p = argparse.ArgumentParser(description="Measure all-device disk activity without a log file")
    p.add_argument("--seconds", type=float, default=60.0)
    p.add_argument("--disks", nargs="+", default=["sda", "sdb"])
    args = p.parse_args()
    if not 5 <= args.seconds <= 3600:
        p.error("--seconds must be 5..3600")
    start = time.monotonic()
    first = read()
    time.sleep(args.seconds)
    seconds = time.monotonic() - start
    last = read()
    result = rates(first, last, seconds)
    print(json.dumps({"elapsed_seconds": round(seconds, 2),
                      "disks": {d: result[d] for d in args.disks if d in result},
                      "warning": "all-process disk counters; compare runs with other workloads held constant"},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
