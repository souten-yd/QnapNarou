#!/usr/bin/env python3
"""Bind QnapNarou Home Screen icon to pinned upstream Narou Web UI at :8888.

Requires an upstream native Rust compile; failures must be explicit on drift.
No QTS runtime image processing, no new server routes at the QNAP manager.
"""
from pathlib import Path
from PIL import Image

HEAD_ANCHOR = '    <title>Narou.rs WEB UI</title>'
ASSET_ANCHOR = '        "js/ui/render.js" => ('
ASSET_SOURCE = '            "application/javascript; charset=utf-8",'
RUST_HANDLER = 'pub async fn asset(Path(path): Path<String>) -> Response {'
RUST_ARM = '''        "qnapnarou-icon.png" => (
            "image/png",
            Cow::Borrowed(include_bytes!("assets/qnapnarou-icon.png").as_slice()),
        ),
'''
TAG = '    <link rel="apple-touch-icon" sizes="180x180" href="/assets/qnapnarou-icon.png">'
SOURCE = Path(__file__).resolve().parents[1] / "assets/qnapnarou-approved.jpg"


def patched_index(source):
    if source.count(HEAD_ANCHOR) != 1:
        raise ValueError("upstream HTML title/head drift")
    if TAG in source:
        raise ValueError("QNAP touch icon already applied")
    return source.replace(HEAD_ANCHOR, HEAD_ANCHOR + "\n" + TAG, 1)


def patched_frontend(source):
    if source.count(RUST_HANDLER) != 1 or source.count(ASSET_ANCHOR) != 1:
        raise ValueError("upstream embedded-asset route drift")
    if RUST_ARM.strip() in source:
        raise ValueError("QNAP embedded icon route already applied")
    # New arm is adjacent to existing embedded assets and has no filesystem
    # reads at runtime: Narou serves the PNG directly from its Rust binary.
    return source.replace(ASSET_ANCHOR, RUST_ARM + ASSET_ANCHOR, 1)


def patch_native_upstream(root: Path):
    root = Path(root)
    frontend = root / "src/web/frontend.rs"
    index = root / "src/web/assets/index.html"
    img = root / "src/web/assets/qnapnarou-icon.png"
    if img.exists():
        raise ValueError("QNAP native icon already exists in upstream checkout")
    # Validate both before mutating either.
    new_frontend = patched_frontend(frontend.read_text(encoding="utf-8"))
    new_index = patched_index(index.read_text(encoding="utf-8"))
    if not SOURCE.is_file():
        raise ValueError("approved QNAP icon source missing")
    with Image.open(SOURCE) as original:
        image = original.convert("RGB").resize((180, 180), Image.Resampling.LANCZOS)
        img.parent.mkdir(parents=True, exist_ok=True)
        image.save(img, "PNG", optimize=True)
    frontend.write_text(new_frontend, encoding="utf-8")
    index.write_text(new_index, encoding="utf-8")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    args = p.parse_args()
    patch_native_upstream(args.source)
