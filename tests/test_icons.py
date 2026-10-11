import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
from tools.build_icons import generate, SOURCE


class QnapIconTests(unittest.TestCase):
    def test_approved_image_and_qdk_outputs(self):
        self.assertTrue(SOURCE.is_file())
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            generate(root)
            for path, fmt, dimensions in [
                ("icons/QnapNarou.gif", "GIF", (64, 64)),
                ("icons/QnapNarou_gray.gif", "GIF", (64, 64)),
                ("icons/QnapNarou_80.gif", "GIF", (80, 80)),
                ("shared/apple-touch-icon.png", "PNG", (180, 180)),
                ("shared/icon-192.png", "PNG", (192, 192)),
                ("shared/favicon.png", "PNG", (32, 32)),
            ]:
                with Image.open(root / path) as image:
                    self.assertEqual(image.format, fmt, path)
                    self.assertEqual(image.size, dimensions, path)
            with Image.open(root / "icons/QnapNarou_gray.gif") as gray:
                self.assertEqual(gray.convert("RGB").getpixel((32, 32))[0],
                                 gray.convert("RGB").getpixel((32, 32))[1])

    def test_missing_source_fails_not_default_icons(self):
        with tempfile.TemporaryDirectory() as d:
            with patch("tools.build_icons.SOURCE", Path(d) / "missing.jpg"):
                with self.assertRaises(ValueError):
                    generate(Path(d) / "out")


class PortalIconTests(unittest.TestCase):
    def test_html_declares_ios_icon_and_manifest(self):
        from tools.manager import html_page
        html = html_page("nonce")
        self.assertIn('rel="apple-touch-icon"', html)
        self.assertIn('href="/manifest.webmanifest"', html)
        self.assertIn('env(safe-area-inset-top', html)
        self.assertIn('href="/favicon.png"', html)

    def test_static_allowlist_does_not_include_library_files(self):
        from tools.manager import ICON_ENDPOINTS
        self.assertEqual(set(ICON_ENDPOINTS), {
            "/apple-touch-icon.png", "/icon-192.png", "/favicon.png"
        })


if __name__ == "__main__":
    unittest.main()
