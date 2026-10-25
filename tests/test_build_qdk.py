import os
from pathlib import Path
import tempfile
import unittest

from tools.build_qdk import prepare


class QdkTests(unittest.TestCase):
    def test_prepare_includes_complete_runtime(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / "runtime"
            src.mkdir()
            for name in ("narou_rs", "narou_rs_updater.new", "narou_rs_backup", "narou_rs_login", "LICENSE", "README.md", "Third-Party-License.md", "commitversion"):
                (src / name).write_text(name)
            for name in ("narou_rs", "narou_rs_updater.new", "narou_rs_backup", "narou_rs_login"):
                os.chmod(src / name, 0o755)
            for name in ("webnovel", "preset"):
                (src / name).mkdir()
                (src / name / "example.txt").write_text("example")
            out = root / "qdk-build"
            prepare(src, out)
            self.assertTrue((out / "x86_64/runtime/narou_rs").exists())
            self.assertTrue((out / "shared/QnapNarou.sh").stat().st_mode & 0o111)
            self.assertTrue((out / "shared/ensure_ws.sh").stat().st_mode & 0o111)
            self.assertTrue((out / "shared/configure_hosts.py").is_file())
            self.assertTrue((out / "shared/io_probe.py").is_file())
            self.assertEqual((out / "x86_64/runtime/preset/example.txt").read_text(), "example")


if __name__ == "__main__":
    unittest.main()
