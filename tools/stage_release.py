#!/usr/bin/env python3
"""Validate and stage an upstream narou.rs release payload without dropping files."""
import argparse
from pathlib import Path
import shutil
import sys

REQUIRED_FILES = (
    "narou_rs", "narou_rs_updater.new", "narou_rs_backup", "narou_rs_login",
    "LICENSE", "README.md", "Third-Party-License.md", "commitversion"
)
REQUIRED_DIRS = ("webnovel", "preset")


def verify_source(source: Path) -> None:
    if not source.is_dir() or source.is_symlink():
        raise ValueError(f"missing or unsafe runtime directory: {source}")
    for name in REQUIRED_FILES:
        p = source / name
        if not p.is_file() or p.is_symlink():
            raise ValueError(f"missing/unsafe runtime file: {name}")
    for name in REQUIRED_DIRS:
        p = source / name
        if not p.is_dir() or p.is_symlink() or not any(x.is_file() for x in p.rglob("*")):
            raise ValueError(f"missing/empty runtime directory: {name}")
    for p in source.rglob("*"):
        if p.is_symlink():
            raise ValueError(f"symlinks forbidden: {p.relative_to(source)}")
    for name in ("narou_rs", "narou_rs_updater.new", "narou_rs_backup", "narou_rs_login"):
        if not (source / name).stat().st_mode & 0o111:
            raise ValueError(f"runtime executable bit missing: {name}")


def stage(source: Path, dest: Path) -> None:
    verify_source(source)
    resolved_src, resolved_dest = source.resolve(), dest.resolve()
    if resolved_src == resolved_dest or resolved_src in resolved_dest.parents:
        raise ValueError("destination must not be inside source")
    if dest.exists() or dest.is_symlink():
        raise ValueError("destination already exists")
    # Copy the ENTIRE upstream runtime, not an ad hoc subset.
    # Upstream may add web assets, site definitions, and licenses.
    try:
        shutil.copytree(source, dest, symlinks=False)
        verify_source(dest)
    except BaseException:
        if dest.is_dir():
            shutil.rmtree(dest)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--dest", type=Path, required=True)
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
