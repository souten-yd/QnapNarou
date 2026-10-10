#!/usr/bin/env python3
"""Verified, tokenless QnapNarou QPKG updater.

Only GitHub-generated asset digests are accepted. Never accepts a URL, command,
filename, or architecture from an HTTP request. Called as a detached NAS worker.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from urllib.parse import quote, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

try:
    from tools.update_check import RELEASE_API, MAX_BYTES, validate_release, parse_version
except ModuleNotFoundError:
    from update_check import RELEASE_API, MAX_BYTES, validate_release, parse_version

ALLOWED_HOSTS = frozenset({"github.com", "api.github.com", "release-assets.githubusercontent.com",
                           "objects.githubusercontent.com"})
MAX_PACKAGE_BYTES = 2_000_000_000
STATUS_DIR = Path("/dev/shm/QnapNarou")
STATUS_FILE = STATUS_DIR / "update-status.json"
LOCK_FILE = STATUS_DIR / "update.lock"


class RestrictedRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urlparse(newurl)
        if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
            raise ValueError("untrusted GitHub release redirect")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def opener():
    return build_opener(RestrictedRedirect)


def fetch_release(tag=None, open_url=None):
    url = RELEASE_API if tag is None else (
        "https://api.github.com/repos/souten-yd/QnapNarou/releases/tags/" + quote(tag, safe=""))
    request = Request(url, headers={"Accept": "application/vnd.github+json",
                                    "User-Agent": "QnapNarou-verified-updater"})
    client = open_url or opener().open
    with client(request, timeout=15) as response:
        if response.status != 200:
            raise ValueError("GitHub release API returned non-200 status")
        data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("GitHub release metadata too large")
    return json.loads(data)


def architecture():
    arch = platform.machine().lower()
    if arch in ("x86_64", "amd64"):
        return "x86_64"
    if arch in ("aarch64", "arm64"):
        return "arm_64"
    raise ValueError("unsupported QNAP CPU architecture")


def plan(current, arch, latest, old_release):
    new = validate_release(latest, current, arch)
    if not new["update_available"]:
        raise ValueError("no newer stable QPKG release")
    old = validate_release(old_release, current, arch)
    if parse_version(old["latest_version"]) != parse_version(current):
        raise ValueError("rollback package version mismatch")
    return old, new


def download_package(info, dest, open_url=None):
    if dest.exists() or dest.is_symlink():
        raise ValueError("refusing to overwrite staged package")
    if not 1024 <= info["asset_size"] <= MAX_PACKAGE_BYTES:
        raise ValueError("release asset outside allowed size")
    if len(info["sha256"]) != 64:
        raise ValueError("invalid digest")
    client = open_url or opener().open
    req = Request(info["download_url"], headers={"User-Agent": "QnapNarou-verified-updater"})
    digest = hashlib.sha256()
    received = 0
    try:
        with client(req, timeout=30) as response:
            if response.status != 200:
                raise ValueError("download returned non-200")
            if urlparse(response.geturl()).hostname not in ALLOWED_HOSTS:
                raise ValueError("untrusted release content host")
            with dest.open("xb") as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    received += len(chunk)
                    if received > info["asset_size"] or received > MAX_PACKAGE_BYTES:
                        raise ValueError("package exceeds verified size")
                    digest.update(chunk)
                    output.write(chunk)
                output.flush()
                os.fsync(output.fileno())
        if received != info["asset_size"] or digest.hexdigest() != info["sha256"]:
            raise ValueError("downloaded QPKG failed length/SHA-256 check")
    except BaseException:
        dest.unlink(missing_ok=True)
        raise


def write_status(phase, detail=""):
    STATUS_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    tmp = STATUS_DIR / "update-status.tmp"
    tmp.write_text(json.dumps({"phase": phase, "detail": detail}, ensure_ascii=False))
    os.replace(tmp, STATUS_FILE)


def apply_update(current, arch, staging, *, run_command=None, fetch=None, download=None):
    run_command = run_command or subprocess.run
    fetch = fetch or fetch_release
    download = download or download_package
    # A previous, checksum-verified release is mandatory for rollback.
    old, new = plan(current, arch, fetch(), fetch("v" + current.lstrip("v")))
    staging.mkdir(mode=0o700, parents=True, exist_ok=True)
    before = staging / old["asset_name"]
    after = staging / new["asset_name"]
    if before == after:
        raise ValueError("old and new packages must be distinct")
    # No reuse of stale or unverified package downloads.
    for candidate in (before, after):
        if candidate.exists() or candidate.is_symlink():
            raise ValueError("update staging requires empty destinations")
    try:
        write_status("downloading", "Retrieving current version for rollback")
        download(old, before)
        write_status("downloading", "Retrieving next version")
        download(new, after)
        write_status("installing", "Applying verified QPKG via QTS")
        command = ["/sbin/qpkg_cli", "-m", str(after), "-q", "-K"]
        try:
            run_command(command, check=True, timeout=1200)
        except BaseException:
            write_status("rollback", "Upgrade failed, reinstalling previous verified QPKG")
            try:
                run_command(["/sbin/qpkg_cli", "-m", str(before), "-q", "-K"], check=True, timeout=1200)
            except BaseException as rollback_error:
                raise RuntimeError("upgrade AND rollback failed; manual recovery required") from rollback_error
            raise RuntimeError("upgrade failed; previous version restored")
        write_status("complete", "QPKG updater finished")
    finally:
        # Clean up both staged packages even if download fails halfway.
        # Never touch the novel library or user settings.
        for candidate in (before, after):
            candidate.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", required=True)
    parser.add_argument("--staging", type=Path, required=True)
    args = parser.parse_args()
    try:
        current = ".".join(map(str, parse_version(args.current)))
        arch = architecture()
        if not STATUS_DIR.is_dir() or not os.access(STATUS_DIR, os.W_OK):
            raise ValueError("RAM status directory /dev/shm/QnapNarou unavailable")
        with LOCK_FILE.open("a+") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            apply_update(current, arch, args.staging)
    except BaseException as exc:
        write_status("failed", str(exc)[:240])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
