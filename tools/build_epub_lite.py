#!/usr/bin/env python3
"""Build the pinned narou.rs GPL/lite variant for QnapNarou.

Does not change the submodule gitlink; the source-only QNAP workaround is
verified against a known upstream structure and applied in the CI checkout.
"""
import argparse
import os
from pathlib import Path
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

# Upstream render.js is embedded with include_str! at Rust compile time.
# Preserve the novel-list page on iPhone by requesting a real download.
# target=_blank provides a recoverable tab if the download attribute is ignored.
DOWNLOAD_ANCHOR = 'class="row-action-btn btn-download" title="書籍データをダウンロード"'
FIXED_DOWNLOAD_ANCHOR = (
    'download target="_blank" rel="noopener noreferrer" '
    + DOWNLOAD_ANCHOR
)


def corrected_download_ui(source):
    if source.count(DOWNLOAD_ANCHOR) != 1:
        raise ValueError("upstream download-link markup drift: expected exactly one anchor")
    if '/novels/${encodeURIComponent(String(novel.id))}/download' not in source:
        raise ValueError("upstream EPUB download route has changed")
    if FIXED_DOWNLOAD_ANCHOR in source:
        raise ValueError("QNAP Safari download patch already applied")
    return source.replace(DOWNLOAD_ANCHOR, FIXED_DOWNLOAD_ANCHOR, 1)



def corrected_web_source(source):
    if source.count(START) != 1 or source.count(END) != 1:
        raise ValueError("upstream EPUB handler drift: expected markers missing/duplicated")
    start = source.index(START)
    end = source.index(END, start)
    old = source[start:end]
    if BAD_RETURN not in old or "novel_outputs" not in old:
        raise ValueError("upstream EPUB handler drift: cached text path no longer matches")
    if "#[cfg(feature = \"lite\")]" not in source[:start]:
        raise ValueError("only apply this workaround to lite-enabled EPUB handler")
    return source[:start] + FIX_COMMENT + source[end:]


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
