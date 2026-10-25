#!/usr/bin/env python3
"""Build the pinned narou.rs GPL/lite variant for QnapNarou.

Does not change the submodule gitlink; the source-only QNAP workaround is
verified against a known upstream structure and applied in the CI checkout.
"""
import argparse
import os
from pathlib import Path
try:
    from tools.build_narou_home_icon import patch_native_upstream
except ModuleNotFoundError:
    from build_narou_home_icon import patch_native_upstream
import shutil
import subprocess
import sys

START = "    // P4a: prefer the SQLite mirror of the converted text when present."
END = "    let keep_text = crate::converter::keep_converted_text_file();"
BAD_RETURN = "return Ok((payload, filename));"
FIX_COMMENT = (
    "    // QNAP fix: the SQLite converted_text payload is Aozora TEXT, not an EPUB.\n"
    "    // Fall through to the real EPUB builder below instead of sending text\n"
    "    // with an .epub filename. Upstream narou.rs is kept as a pinned gitlink.\n"
)
GPL_LICENSE = "GPL-3.0-only"

# The upstream Web UI is embedded with include_str! in a Rust binary. The
# QNAP-owned handler is injected at native build time, never copied to a live
# QTS data folder. Refuse unknown upstream markup rather than silently lose
# the fix when the pinned submodule is updated.
DOWNLOAD_ROUTE = '/novels/${encodeURIComponent(String(novel.id))}/download'
DOWNLOAD_ANCHOR = 'class="row-action-btn btn-download" title="書籍データをダウンロード"'
FIXED_DOWNLOAD_ANCHOR = 'data-qnap-epub="1" ' + DOWNLOAD_ANCHOR
OVERLAY_MARKER = "QnapNarou EPUB save/share overlay."
OVERLAY_PATH = Path(__file__).with_name("qnap_epub_download.js")


def corrected_download_ui(source, overlay=None):
    if overlay is None:
        overlay = OVERLAY_PATH.read_text(encoding="utf-8")
    if source.count(DOWNLOAD_ANCHOR) != 1:
        raise ValueError("upstream download-link markup drift: expected exactly one anchor")
    position = source.index(DOWNLOAD_ANCHOR)
    if DOWNLOAD_ROUTE not in source[max(0, position - 200):position]:
        raise ValueError("upstream EPUB download route has changed")
    if FIXED_DOWNLOAD_ANCHOR in source or OVERLAY_MARKER in source:
        raise ValueError("QNAP EPUB overlay already applied")
    if overlay.count(OVERLAY_MARKER) != 1 or not all(
        item in overlay for item in (
            "event.preventDefault()", "event.stopImmediatePropagation()",
            "navigator.canShare", "navigator.share", "URL.createObjectURL",
            "fetch(url.href", "data-qnap-epub"
        )
    ):
        raise ValueError("missing or incomplete QNAP EPUB save/share overlay")
    # Validation precedes any source changes. Rust recompilation embeds the
    # UI on every reviewed upstream gitlink update; old QPKG binaries are not
    # modified in place.
    return source.replace(DOWNLOAD_ANCHOR, FIXED_DOWNLOAD_ANCHOR, 1) + "\n" + overlay + "\n"


def corrected_web_source(source):
    """Remove the legacy bad fast path, or verify v0.5.3's fixed EPUB path."""
    if source.count(START) != 1 or source.count(END) != 1:
        raise ValueError("upstream EPUB handler drift: expected markers missing/duplicated")
    start = source.index(START)
    end = source.index(END, start)
    old = source[start:end]
    if '#[cfg(feature = "lite")]' not in source[:start]:
        raise ValueError("only apply the workaround to lite-enabled EPUB handler")
    if BAD_RETURN in old:
        if "novel_outputs" not in old:
            raise ValueError("upstream cached text fast path changed")
        return source[:start] + FIX_COMMENT + source[end:]
    # Reviewed upstream v0.5.3 converts cached UTF-8 text into a real EPUB;
    # no longer patch that fixed path. Never accept an arbitrary unknown path.
    safe_markers = (
        "let cached_text = if keep_text",
        "String::from_utf8(payload)",
        "`converted_text` contains UTF-8 text, never EPUB bytes.",
    )
    if not all(m in old for m in safe_markers) or "build_book" not in source[end:]:
        raise ValueError("upstream EPUB handler changed; review required")
    return source


def ensure_pinned(repo):
    root = repo.parent.parent
    expected = subprocess.check_output(
        ["git", "rev-parse", ":upstream/narou.rs"], cwd=root, text=True).strip()
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    if expected != actual:
        raise ValueError("source checkout differs from pinned upstream gitlink")
    changed = subprocess.check_output(["git", "status", "--porcelain"], cwd=repo, text=True)
    if changed.strip():
        raise ValueError("upstream source has uncommitted changes")
    return expected


def patch(repo):
    ensure_pinned(repo)
    file = repo / "src/web/novels.rs"
    original = file.read_text(encoding="utf-8")
    replacement = corrected_web_source(original)
    ui_file = repo / "src/web/assets/js/ui/render.js"
    original_ui = ui_file.read_text(encoding="utf-8")
    fixed_ui = corrected_download_ui(original_ui)
    # Validate both source patches before changing either file.
    file.write_text(replacement, encoding="utf-8")
    ui_file.write_text(fixed_ui, encoding="utf-8")


def build(repo, runtime, target):
    if target != "x86_64-unknown-linux-musl":
        raise ValueError("Only tested x86_64 musl is supported; no implicit ARM build")
    if not (runtime / "narou_rs").is_file():
        raise ValueError("run cargo local-build first to generate the complete narou/ layout")
    if not (repo / "Third-Party-License.md").is_file():
        raise ValueError("GPL third-party notices missing")
    if not (repo / "assets/aozora_lite/LICENSE.md").is_file():
        raise ValueError("AozoraEpub3_Lite license missing")

    patch(repo)
    patch_native_upstream(repo)
    env = os.environ.copy()
    env["NAROU_RS_RELEASE_BUILD"] = "1"
    env["NAROU_RS_LOCAL_BUILD"] = "1"
    subprocess.run(
        ["cargo", "build", "--locked", "--release", "--features", "lite",
         "--target", target, "--bin", "narou_rs"],
        cwd=repo, env=env, check=True
    )
    binary = repo / "target" / target / "release" / "narou_rs"
    if not binary.is_file() or not (binary.stat().st_mode & 0o111):
        raise ValueError("GPL/lite release binary missing")
    shutil.copy2(binary, runtime / "narou_rs")
    shutil.copy2(repo / "Third-Party-License.md", runtime / "Third-Party-License.md")
    shutil.copy2(repo / "assets/aozora_lite/LICENSE.md", runtime / "AozoraEpub3-Lite-License.md")
    (runtime / "QnapNarou-Build-Variant.txt").write_text(
        "QnapNarou GPL-3.0-only (narou.rs lite feature / AozoraEpub3_Lite)\n",
        encoding="utf-8"
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--runtime", type=Path, required=True)
    p.add_argument("--target", required=True)
    args = p.parse_args()
    try:
        build(args.source.resolve(), args.runtime.resolve(), args.target)
    except (OSError, ValueError, subprocess.CalledProcessError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
