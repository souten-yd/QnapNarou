#!/usr/bin/env python3
"""Prepare a QDK build environment from fully staged upstream runtime.

Requires installed QDK's qbuild for QPKG output; no CI build or downloads.
"""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
try:
    from tools.stage_release import verify_source
    from tools.build_icons import generate as generate_icons
except ModuleNotFoundError:  # direct execution from repository root
    from stage_release import verify_source
    from build_icons import generate as generate_icons


def prepare(runtime: Path, out: Path):
    verify_source(runtime)
    if out.exists():
        raise ValueError("build root already exists; choose a fresh directory")
    template = Path(__file__).resolve().parent.parent / "qdk"
    out.mkdir(parents=True)
    try:
        for name in ("qpkg.cfg", "package_routines"):
            shutil.copy2(template / name, out / name)
        shared = out / "shared"
        shutil.copytree(template / "shared", shared)
        # Persistent QPKG/portal icons are packaged once: no QTS-side image processing.
        generate_icons(out)
        # The management server and updater ship with every QPKG, no pip install.
        for name in ("manager.py", "installer.py", "update_check.py", "configure_hosts.py", "io_probe.py"):
            shutil.copy2(template.parent / "tools" / name, shared / name)
        arch = out / "x86_64" / "runtime"
        arch.parent.mkdir()
        shutil.copytree(runtime, arch)
        (shared / "QnapNarou.sh").chmod(0o755)
        (shared / "ensure_ws.sh").chmod(0o755)
        (out / "package_routines").chmod(0o755)
        verify_source(arch)
    except BaseException:
        shutil.rmtree(out)
        raise


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--runtime", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--build", action="store_true", help="invoke locally installed qbuild")
    args = p.parse_args()
    try:
        prepare(args.runtime, args.out)
        if args.build:
            if not shutil.which("qbuild"):
                raise RuntimeError("qbuild not installed; install QDK first")
            subprocess.run(["qbuild"], cwd=args.out, check=True)
    except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
