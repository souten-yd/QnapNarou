import os
from pathlib import Path
import tempfile
import unittest

from tools.stage_release import stage, verify_source


class StageReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.src = self.root / "source"
        self.src.mkdir()
        for name in ("narou_rs", "narou_rs_updater.new", "narou_rs_backup", "narou_rs_login", "LICENSE", "README.md", "Third-Party-License.md", "commitversion"):
            (self.src / name).write_text(name)
        for name in ("narou_rs", "narou_rs_updater.new", "narou_rs_backup", "narou_rs_login"):
            os.chmod(self.src / name, 0o755)
        for name in ("webnovel", "preset"):
            d = self.src / name
            d.mkdir()
            (d / "example.txt").write_text("payload")

    def test_stage_complete(self):
        dest = self.root / "dest"
        stage(self.src, dest)
        verify_source(dest)
        self.assertEqual((dest / "preset/example.txt").read_text(), "payload")

    def test_preserves_extra_upstream_files(self):
        (self.src / "new_asset.js").write_text("new")
        stage(self.src, self.root / "dest")
        self.assertEqual((self.root / "dest/new_asset.js").read_text(), "new")

    def test_missing_asset_rejected(self):
        (self.src / "commitversion").unlink()
        with self.assertRaises(ValueError):
            stage(self.src, self.root / "dest")

    def test_symlink_rejected(self):
        (self.src / "preset/link").symlink_to(self.src / "LICENSE")
        with self.assertRaises(ValueError):
            stage(self.src, self.root / "dest")

    def test_existing_output_rejected(self):
        dest = self.root / "dest"
        dest.mkdir()
        with self.assertRaises(ValueError):
            stage(self.src, dest)


if __name__ == "__main__":
    unittest.main()
