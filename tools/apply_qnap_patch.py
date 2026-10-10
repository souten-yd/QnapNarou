#!/usr/bin/env python3
"""Explicitly apply QNAP's bounded RAM cache patch to the pinned upstream source.

Run before cargo local-build. Fails closed if upstream drifts or checkout is dirty.
"""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
UPSTREAM = ROOT / "upstream/narou.rs"
PATCH = ROOT / "patches/sqlite-ram-cache.patch"


def git(*argv, cwd=ROOT):
    return subprocess.run(["git", *argv], cwd=cwd, capture_output=True,
                          text=True, check=True).stdout.strip()


def apply():
    pinned = git("rev-parse", ":upstream/narou.rs")
    actual = git("rev-parse", "HEAD", cwd=UPSTREAM)
    if actual != pinned:
        raise ValueError("upstream checkout does not match pinned Gitlink")
    if git("status", "--porcelain", cwd=UPSTREAM):
        raise ValueError("upstream checkout already modified; patch must be applied once")
    if not PATCH.is_file():
        raise ValueError("QNAP cache patch missing")
    git("apply", "--check", str(PATCH), cwd=UPSTREAM)
    git("apply", str(PATCH), cwd=UPSTREAM)
    print(f"QNAP bounded SQLite RAM cache patch applied to pinned {pinned}")


if __name__ == "__main__":
    try:
        apply()
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        raise SystemExit(1)
