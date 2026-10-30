"""v0.1.14 parser-regression release invariants."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
class V0114Tests(unittest.TestCase):
    def test_release_requires_native_parser_regression(self):
        wf = (ROOT / '.github/workflows/qnapnarou-release-v0114.yml').read_text()
        self.assertIn('QPKG_VER="0.1.14"', (ROOT / 'qdk/qpkg.cfg').read_text())
        for token in ['qnap_preprocess_stack_tests', 'test result: ok', '2 passed',
                      'patch_preprocess_parser.py', 'QNAP_PREPROCESS_STACK_FIX',
                      'gh release create v0.1.14', 'sha256sum -c dist/SHA256SUMS',
                      '47bee6ba703441d3aa989e29694e3df485c4c643']:
            self.assertIn(token, wf)
        self.assertNotIn('schedule:', wf)
    def test_runtime_wrapper_is_unchanged_in_behavior(self):
        sh = (ROOT / 'qdk/shared/QnapNarou.sh').read_text()
        self.assertIn('NAROU_RS_DISABLE_SELF_UPDATE=1', sh)
        self.assertNotIn('NAROU_RS_QNAP_MEMORY_CACHE', sh)
if __name__ == '__main__':
    unittest.main()
