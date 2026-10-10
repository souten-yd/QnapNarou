#!/usr/bin/env python3
"""Read-only public GitHub release availability check (no token, no install).

This helper does not execute downloaded content or modify application state.
"""
import argparse
import json
import re
import sys
from urllib.request import Request, urlopen

RELEASE_API = "https://api.github.com/repos/souten-yd/QnapNarou/releases/latest"
VERSION = re.compile(r"^v?([0-9]+)\.([0-9]+)\.([0-9]+)$")
MAX_BYTES = 256 * 1024


def parse_version(version):
    match = VERSION.fullmatch(version)
    if not match:
        raise ValueError("Only stable semantic versions X.Y.Z are supported")
    return tuple(int(v) for v in match.groups())


def validate_release(doc, current, arch):
    if not isinstance(doc, dict) or doc.get("draft") or doc.get("prerelease"):
        raise ValueError("no stable published release")
    tag = doc.get("tag_name", "")
    latest = parse_version(tag)
    current_version = parse_version(current)
    assets = doc.get("assets")
    if not isinstance(assets, list):
        raise ValueError("missing release assets")
    filename = "QnapNarou_" + arch + "_" + tag.lstrip("v") + ".qpkg"
    matching = [asset for asset in assets if isinstance(asset, dict) and asset.get("name") == filename]
    if len(matching) != 1:
        raise ValueError("release lacks exactly one matching QPKG artifact")
    asset = matching[0]
    download = asset.get("browser_download_url", "")
    expected_prefix = "https://github.com/souten-yd/QnapNarou/releases/download/"
    if not isinstance(download, str) or not download.startswith(expected_prefix):
        raise ValueError("asset download URL is not from trusted repository")
    if not download.endswith("/" + filename):
        raise ValueError("unexpected asset filename")
    if not isinstance(asset.get("size"), int) or not (1024 <= asset["size"] <= 2_000_000_000):
        raise ValueError("invalid asset size")
    return {"current_version": current, "latest_version": tag, "update_available": latest > current_version,
            "architecture": arch, "asset_name": filename, "download_url": download,
            "note": "Update installation is not implemented: do not download or execute from this checker."}


def fetch_release():
    request = Request(RELEASE_API, headers={"Accept": "application/vnd.github+json",
                                            "User-Agent": "QnapNarou-update-check"})
    with urlopen(request, timeout=8) as response:
        if response.status != 200:
            raise ValueError("release API returned unexpected status")
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("release metadata too large")
        return json.loads(raw)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", required=True)
    parser.add_argument("--arch", choices=["x86_64", "arm_64"], required=True)
    args = parser.parse_args()
    try:
        result = validate_release(fetch_release(), args.current, args.arch)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
