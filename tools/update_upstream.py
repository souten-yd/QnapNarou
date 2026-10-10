#!/usr/bin/env python3
"""Manual, reviewable upstream narou.rs sync. Never auto-merges or builds on idle."""
import argparse
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
SUBMODULE = ROOT / "upstream" / "narou.rs"


def git(*args, cwd=ROOT, check=True):
    return subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=check)


def require_clean():
    for cwd in (ROOT, SUBMODULE):
        if git("status", "--porcelain", cwd=cwd).stdout.strip():
            raise ValueError(f"repository has uncommitted changes: {cwd}")


def update(*, apply=False, target=None):
    if not (SUBMODULE / ".git").exists():
        raise ValueError("upstream submodule is not initialized: run git submodule update --init")
    require_clean()
    current = git("rev-parse", "HEAD", cwd=SUBMODULE).stdout.strip()
    git("fetch", "--no-tags", "origin", "main", cwd=SUBMODULE)
    latest = git("rev-parse", "origin/main", cwd=SUBMODULE).stdout.strip()
    if len(current) != 40 or len(latest) != 40:
        raise ValueError("invalid upstream revision")
    changed = current != latest
    print(f"Pinned upstream: {current}\nUpstream main:   {latest}")
    if not changed:
        print("Already up to date")
        return False
    ancestor = git("merge-base", "--is-ancestor", current, latest, cwd=SUBMODULE, check=False)
    if ancestor.returncode != 0:
        raise ValueError("upstream main is not a fast-forward; review history manually")
    print("Review upstream changelog and source/API changes before applying.")
    print(git("log", "--oneline", f"{current}..{latest}", cwd=SUBMODULE).stdout)
    if not apply:
        print("Dry run only; use --apply --expected-sha " + latest)
        return True
    if target != latest:
        raise ValueError("--expected-sha must exactly match the fetched upstream main")
    git("checkout", "--detach", latest, cwd=SUBMODULE)
    git("add", "upstream/narou.rs")
    print(git("diff", "--cached", "--submodule=log", "--", "upstream/narou.rs").stdout)
    print("Review and commit the staged gitlink on a feature branch; open a PR.")
    print("No auto-merge, runtime mutation or background CI was performed.")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--expected-sha", default=None)
    args = parser.parse_args()
    if args.apply and not args.expected_sha:
        parser.error("--apply requires --expected-sha")
    try:
        update(apply=args.apply, target=args.expected_sha)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
