#!/usr/bin/env python3
"""Review a tagged upstream source and explicitly stage a pinned gitlink change."""
import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UPSTREAM = ROOT / "upstream/narou.rs"


def git(*args, cwd=ROOT, check=True):
    return subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=check)


def sync(tag, expected_sha=None, apply=False):
    if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", tag):
        raise ValueError("use a versioned release tag vX.Y.Z")
    if apply and (expected_sha is None or not re.fullmatch(r"[0-9a-f]{40}", expected_sha)):
        raise ValueError("--apply requires an explicit 40-character reviewed SHA")
    if not (UPSTREAM / ".git").exists():
        raise ValueError("initialize upstream submodule first")
    for path in (ROOT, UPSTREAM):
        if git("status", "--porcelain", cwd=path).stdout.strip():
            raise ValueError(f"working tree is dirty: {path}")
    pinned = git("rev-parse", ":upstream/narou.rs").stdout.strip()
    actual = git("rev-parse", "HEAD", cwd=UPSTREAM).stdout.strip()
    if pinned != actual or not re.fullmatch(r"[0-9a-f]{40}", pinned):
        raise ValueError("pinned submodule and checked-out source differ")
    git("fetch", "--tags", "origin", cwd=UPSTREAM)
    tagged = git("rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}", cwd=UPSTREAM).stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", tagged):
        raise ValueError("invalid upstream tagged SHA")
    if git("merge-base", "--is-ancestor", pinned, tagged, cwd=UPSTREAM, check=False).returncode:
        raise ValueError("non-fast-forward upstream history; manual audit required")
    print(f"Pinned upstream: {pinned}\nTagged {tag}: {tagged}")
    if pinned == tagged:
        print("Already pinned")
        return False
    print(git("log", "--oneline", f"{pinned}..{tagged}", cwd=UPSTREAM).stdout)
    if not apply:
        print(f"Dry run: review source, then --apply --expected-sha {tagged}")
        return True
    if expected_sha != tagged:
        raise ValueError("reviewed SHA does not equal fetched tag commit")
    git("checkout", "--detach", tagged, cwd=UPSTREAM)
    git("add", "upstream/narou.rs")
    print(git("diff", "--cached", "--submodule=log", "--", "upstream/narou.rs").stdout)
    print("Create reviewed PR; don't merge or release automatically.")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--expected-sha")
    a = parser.parse_args()
    try:
        sync(a.tag, a.expected_sha, a.apply)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
