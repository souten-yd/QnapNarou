"""Guard the new pinned native release from silent regression."""
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SHA = "47bee6ba703441d3aa989e29694e3df485c4c643"
class Release013Tests(unittest.TestCase):
    def test_release_pins_and_qdk(self):
        wf = (ROOT / ".github/workflows/qnapnarou-release-v0113.yml").read_text()
        self.assertIn('QPKG_VER="0.1.14"', (ROOT / 'qdk/qpkg.cfg').read_text())
        for item in (SHA, 'refs/tags/v0.5.5^{commit}', 'gh release create v0.1.13',
                     'sha256sum -c dist/SHA256SUMS', 'cargo local-build --locked',
                     'cmp tools/io_probe.py build/qdk/shared/io_probe.py'):
            self.assertIn(item, wf)
        self.assertIn("paths: [.github/workflows/qnapnarou-release-v0113.yml]", wf)
        self.assertNotIn('schedule:', wf)
        self.assertNotIn('tools/apply_qnap_patch.py', wf)

    def test_qnap_wrapper_is_not_experimental(self):
        shell = (ROOT / "qdk/shared/QnapNarou.sh").read_text()
        self.assertIn('NAROU_RS_DISABLE_SELF_UPDATE=1', shell)
        self.assertIn('PYTHONDONTWRITEBYTECODE=1', shell)
        self.assertNotIn('NAROU_RS_QNAP_MEMORY_CACHE', shell)
        self.assertTrue((ROOT / "docs/release-v0113.md").is_file())

if __name__ == '__main__':
    unittest.main()
