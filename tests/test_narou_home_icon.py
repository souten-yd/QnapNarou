import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from PIL import Image

from tools.build_narou_home_icon import (
    patched_frontend, patched_index, patch_native_upstream, HEAD_ANCHOR,
    ASSET_ANCHOR, RUST_HANDLER, TAG
)


class NarouHomeIconTests(unittest.TestCase):
    def test_upstream_index_gets_apple_touch_icon(self):
        html = "<html><head>\n" + HEAD_ANCHOR + "\n</head></html>"
        patched = patched_index(html)
        self.assertIn(TAG, patched)
        self.assertEqual(patched.count(TAG), 1)
        with self.assertRaises(ValueError):
            patched_index(patched)

    def test_rust_route_is_embedded_and_guarded(self):
        code = RUST_HANDLER + "\n  match path.as_str() {\n" + ASSET_ANCHOR + "\n}"
        patched = patched_frontend(code)
        self.assertIn("image/png", patched)
        self.assertIn('include_bytes!("assets/qnapnarou-icon.png")', patched)
        with self.assertRaises(ValueError):
            patched_frontend(patched)
        with self.assertRaises(ValueError):
            patched_frontend(code.replace(ASSET_ANCHOR, "other arm"))

    def test_compile_source_generation_without_qts_disk_changes(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "src/web"
            (src / "assets").mkdir(parents=True)
            (src / "frontend.rs").write_text(RUST_HANDLER + "\n" + ASSET_ANCHOR)
            (src / "assets/index.html").write_text(HEAD_ANCHOR)
            patch_native_upstream(root)
            with Image.open(src / "assets/qnapnarou-icon.png") as im:
                self.assertEqual(im.size, (180, 180))
                self.assertEqual(im.format, "PNG")
            with self.assertRaises(ValueError):
                patch_native_upstream(root)

    def test_real_pinned_upstream_when_checkout_exists(self):
        root = Path(__file__).resolve().parents[1] / "upstream/narou.rs"
        if not (root / "src/web/frontend.rs").is_file():
            self.skipTest("upstream submodule not checked out")
        self.assertIn("image/png", patched_frontend(
            (root / "src/web/frontend.rs").read_text()))
        self.assertIn(TAG, patched_index(
            (root / "src/web/assets/index.html").read_text()))


if __name__ == "__main__":
    unittest.main()
