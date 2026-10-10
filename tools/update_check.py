#!/usr/bin/env python3
"""Read-only, tokenless GitHub Releases discovery for QnapNarou.

Releases/latest is 404 when only prereleases exist. Discover /releases and
validate the asset name, size, hash and URL for stable and RC releases.
No installs, scheduled requests or persistent cache.
"""
import argparse
import json
import re
import sys
from urllib.parse import quote
from urllib.request import Request, urlopen

RELEASE_API = "https://api.github.com/repos/souten-yd/QnapNarou/releases/latest"
RELEASES_API = "https://api.github.com/repos/souten-yd/QnapNarou/releases?per_page=20"
VERSION = re.compile(r"^v?([0-9]+)\.([0-9]+)\.([0-9]+)$")
RELEASE_TAG = re.compile(r"^v?([0-9]+)\.([0-9]+)\.([0-9]+)(?:-rc([1-9][0-9]*))?$")
MAX_BYTES = 256 * 1024
REPO_ASSETS = "https://github.com/souten-yd/QnapNarou/releases/download/"


def parse_version(value):
    if not isinstance(value, str):
        raise ValueError("invalid installed version")
    match = VERSION.fullmatch(value)
    if not match:
        raise ValueError("Installed version must use X.Y.Z")
    return tuple(int(part) for part in match.groups())


def release_version(tag):
    if not isinstance(tag, str):
        raise ValueError("invalid release tag")
    match = RELEASE_TAG.fullmatch(tag)
    if not match:
        raise ValueError("Unsupported release tag")
    return tuple(int(part) for part in match.groups()[:3]), (
        int(match.group(4)) if match.group(4) else None)


def validate_release(doc, current, arch, *, allow_prerelease=False):
    if not isinstance(doc, dict) or doc.get("draft") or not doc.get("published_at", True):
        raise ValueError("unpublished or malformed release")
    tag = doc.get("tag_name")
    version, rc = release_version(tag)
    preview = rc is not None
    if bool(doc.get("prerelease")) != preview:
        raise ValueError("release channel does not match tag")
    if preview and not allow_prerelease:
        raise ValueError("no stable published release")
    current_version = parse_version(current)
    if arch not in ("x86_64", "arm_64"):
        raise ValueError("unsupported architecture")
    assets = doc.get("assets")
    if not isinstance(assets, list):
        raise ValueError("missing release assets")
    numbered = ".".join(map(str, version))
    filename = f"QnapNarou_{arch}_{numbered}.qpkg"
    matches = [a for a in assets if isinstance(a, dict) and a.get("name") == filename]
    if len(matches) != 1:
        raise ValueError("release lacks exactly one matching QPKG artifact")
    asset = matches[0]
    expected_url = REPO_ASSETS + quote(tag, safe="") + "/" + filename
    download = asset.get("browser_download_url")
    # GitHub URLs preserve the literal tag value (hyphen and dots).
    literal_url = REPO_ASSETS + tag + "/" + filename
    if download != literal_url:
        raise ValueError("unexpected release download URL")
    size = asset.get("size")
    if type(size) is not int or not 1024 <= size <= 2_000_000_000:
        raise ValueError("invalid asset size")
    digest = asset.get("digest")
    if not isinstance(digest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise ValueError("release asset has no SHA-256 digest")
    return {
        "sha256": digest[7:], "asset_size": size, "current_version": current,
        "latest_version": tag, "update_available": version > current_version,
        "architecture": arch, "asset_name": filename, "download_url": download,
        "prerelease": preview, "version": numbered,
        "note": "Release discovery only; automatic QPKG installation is not device-qualified.",
    }


def summarize_releases(releases, current, arch):
    if not isinstance(releases, list):
        raise ValueError("GitHub release list is malformed")
    parse_version(current)
    valid = []
    for candidate in releases[:20]:
        try:
            validated = validate_release(candidate, current, arch, allow_prerelease=True)
            tag_version, rc = release_version(validated["latest_version"])
            # stable wins for identical numeric version; among previews, newer RC wins.
            valid.append(((tag_version, int(rc is None), rc or 0), validated))
        except (TypeError, ValueError):
            continue
    if not valid:
        return {"current_version": current, "latest_version": None,
                "update_available": False, "prerelease": None,
                "download_url": None, "auto_install_allowed": False,
                "message": "対応する公開QPKGはまだありません。"}
    chosen = max(valid, key=lambda entry: entry[0])[1]
    return {
        "current_version": current, "latest_version": chosen["latest_version"],
        "update_available": chosen["update_available"],
        "prerelease": chosen["prerelease"], "download_url": chosen["download_url"],
        "auto_install_allowed": False,
        "message": ("プレビュー版です。QTSから手動インストールしてください。"
                    if chosen["prerelease"] else
                    "正式版が見つかりました。自動更新はQTS実機検証後に有効化します。"),
    }


def fetch_releases(open_url=urlopen):
    request = Request(RELEASES_API, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "QnapNarou-update-check"})
    with open_url(request, timeout=12) as response:
        if response.status != 200:
            raise ValueError("GitHub Releases API returned unexpected status")
        payload = response.read(MAX_BYTES + 1)
        if len(payload) > MAX_BYTES:
            raise ValueError("GitHub release metadata too large")
    return json.loads(payload)


def fetch_release():
    """Legacy stable-only helper: installer should never promote prereleases."""
    request = Request(RELEASE_API, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "QnapNarou-stable-only"})
    with urlopen(request, timeout=8) as response:
        if response.status != 200:
            raise ValueError("release API returned unexpected status")
        payload = response.read(MAX_BYTES + 1)
        if len(payload) > MAX_BYTES:
            raise ValueError("release metadata too large")
    return json.loads(payload)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", required=True)
    parser.add_argument("--arch", choices=("x86_64", "arm_64"), required=True)
    args = parser.parse_args()
    try:
        result = summarize_releases(fetch_releases(), args.current, args.arch)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
