#!/usr/bin/env python3
"""Deterministically derive QDK + iPhone app icons from the approved asset.

Executed at package build only. No Pillow dependency, disk cache, image
transformation or extra background services on the QNAP device.
"""
from pathlib import Path
from PIL import Image, ImageOps

SOURCE = Path(__file__).resolve().parents[1] / "assets" / "qnapnarou-approved.jpg"
QPKG_NAME = "QnapNarou"


def generate(destination: Path):
    if not SOURCE.is_file():
        raise ValueError("approved icon source is missing")
    destination = Path(destination)
    icons = destination / "icons"
    shared = destination / "shared"
    icons.mkdir(parents=True, exist_ok=True)
    shared.mkdir(parents=True, exist_ok=True)
    with Image.open(SOURCE) as img:
        image = ImageOps.fit(img.convert("RGB"), (512, 512), Image.Resampling.LANCZOS)
        # QDK App Center enabled/disabled/info icons: exact required names/sizes.
        image.resize((64, 64), Image.Resampling.LANCZOS).save(
            icons / "QnapNarou.gif", format="GIF", optimize=True)
        ImageOps.grayscale(image.resize((64, 64), Image.Resampling.LANCZOS)).save(
            icons / "QnapNarou_gray.gif", format="GIF", optimize=True)
        image.resize((80, 80), Image.Resampling.LANCZOS).save(
            icons / "QnapNarou_80.gif", format="GIF", optimize=True)
        # iPhone uses the full-bleed file, iOS applies its own icon mask.
        image.resize((180, 180), Image.Resampling.LANCZOS).save(
            shared / "apple-touch-icon.png", format="PNG", optimize=True)
        image.resize((192, 192), Image.Resampling.LANCZOS).save(
            shared / "icon-192.png", format="PNG", optimize=True)
        image.resize((32, 32), Image.Resampling.LANCZOS).save(
            shared / "favicon.png", format="PNG", optimize=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    generate(args.out)
