"""Release invariants to prevent silent loss of PR #18 and bad SHA paths."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class QnapNarouV0112Tests(unittest.TestCase):
    def test_release_version_and_diagnostic_are_packaged(self):
        self.assertIn('QPKG_VER="0.1.14"', (ROOT / "qdk/qpkg.cfg").read_text())
        self.assertIn('QPKG_LICENSE="GPL-3.0-only"', (ROOT / "qdk/qpkg.cfg").read_text())
        self.assertIn('"configure_hosts.py", "io_probe.py"', (ROOT / "tools/build_qdk.py").read_text())
        for relative in ("tools/io_probe.py", "tests/test_io_probe.py", "docs/low-write.md"):
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_no_sqlite_or_auto_update_change(self):
        sh = (ROOT / "qdk/shared/QnapNarou.sh").read_text()
        self.assertIn("NAROU_RS_DISABLE_SELF_UPDATE=1", sh)
        self.assertIn("PYTHONDONTWRITEBYTECODE=1", sh)
        self.assertNotIn("NAROU_RS_QNAP_MEMORY_CACHE", sh)
        tool = (ROOT / "tools/io_probe.py").read_text()
        self.assertIn('DISKSTATS = Path("/proc/diskstats")', tool)
        self.assertNotIn(".write_text(", tool)
        self.assertNotIn(".write_bytes(", tool)

    def test_release_workflow_uses_correct_sha_manifest_location(self):
        wf = (ROOT / ".github/workflows/qnapnarou-release-v0112.yml").read_text()
        self.assertIn("sha256sum -c dist/SHA256SUMS", wf)
        self.assertNotIn("(cd dist && sha256sum -c SHA256SUMS)", wf)
        self.assertIn("test -s build/qdk/shared/io_probe.py", wf)
        self.assertIn("cmp tools/io_probe.py build/qdk/shared/io_probe.py", wf)
        self.assertIn("gh release create v0.1.12", wf)
        self.assertIn("4c0c15849690b12ee27faf617eabbb863b73d72a", wf)

if __name__ == "__main__":
    unittest.main()
