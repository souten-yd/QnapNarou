#!/usr/bin/env python3
"""Stage the complete upstream runtime for a future QDK package.

This tool deliberately does NOT claim to create a QPKG. QDK packaging and
QTS execution belong to the next milestone.
"""
import argparse
from pathlib import Path
import shutil
import sys

REQUIRED_FILES = ("narou_rs", "LICENSE", "README.md", "Third-Party-License.md", "commitversion")
REQUIRED_DIRS = ("webnovel", "preset")
OPTIONAL_HELPERS = ("narou_rs_updater", "narou_rs_backup", "narou_rs_login")


def verify_source(source: Path) -> None:
    if not source.is_dir():
        raise ValueError(f"runtime directory not found: {source}")
    for name in REQUIRED_FILES:
        p = source / name
        if not p.is_file() or p.is_symlink():
            raise ValueError(f"missing/unsafe runtime file: {name}")
    for name in REQUIRED_DIRS:
        p = source / name
        if not p.is_dir() or p.is_symlink() or not any(p.rglob("*")):
            raise ValueError(f"missing/empty runtime directory: {name}")
    for p in source.rglob("*"):
        if p.is_symlink():
            raise ValueError(f"symlink forbidden in runtime payload: {p.relative_to(source)}")
    if not (source / "narou_rs").stat().st_mode & 0o111:
        raise ValueError("narou_rs is not executable")


def stage(source: Path, dest: Path) -> None:
    verify_source(source)
    if dest.exists():
        raise ValueError("destination exists; choose a fresh staging directory")
    if source.resolve() == dest.resolve() or source.resolve() in dest.resolve().parents:
        raise ValueError("destination must not be within source")
    dest.mkdir(parents=True)
    try:
        for name in (*REQUIRED_FILES, *OPTIONAL_HELPERS):
            p = source / name
            if p.is_file():
                shutil.copy2(p, dest / name)
        for name in REQUIRED_DIRS:
            shutil.copytree(source / name, dest / name, symlinks=False)
    except BaseException:
        shutil.rmtree(dest)
        raise
    verify_source(dest)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True, help="upstream narou/ runtime directory")
    parser.add_argument("--dest", type=Path, required=True, help="new staging directory")
    args = parser.parse_args()
    try:
        stage(args.source, args.dest)
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"staged runtime: {args.dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
