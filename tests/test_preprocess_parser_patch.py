import unittest
from pathlib import Path
from tools.patch_preprocess_parser import (
    rewritten_source, MARKER, ENTRY, NEXT, PINNED_UPSTREAM, EXPECTED_PARSER_BLOB
)

class QnapPreprocessParserPatchTests(unittest.TestCase):
    def test_rewrites_only_reviewed_parser_function(self):
        original = """use pest::Parser;
pub fn parse_preprocess(source: &str) -> Result<Vec<Stmt>, String> {
    let pairs = PreprocessParser::parse(Rule::program, source).unwrap();
    let stmts = Vec::new();
    Ok(stmts)
}
fn build_stmt(pair: Pair) {}
"""
        fixed = rewritten_source(original)
        self.assertIn(MARKER, fixed)
        self.assertIn('stack_size(QNAP_PREPROCESS_STACK_BYTES)', fixed)
        self.assertIn('QNAP_PREPROCESS_MAX_SOURCE_BYTES', fixed)
        self.assertIn('fn parse_preprocess_on_large_stack(', fixed)
        self.assertIn('fn build_stmt(pair: Pair)', fixed)
        self.assertIn('www.pixiv.net.yaml', fixed)
        self.assertIn('www.alphapolis.co.jp.yaml', fixed)
        self.assertIn('mod qnap_preprocess_stack_tests', fixed)
        with self.assertRaises(ValueError):
            rewritten_source(fixed)

    def test_refuses_unknown_parser_shape(self):
        for src in ("", 'pub fn parse_preprocess(source: &str) {}\nfn build_stmt(){}'):
            with self.assertRaises(ValueError):
                rewritten_source(src)

    def test_pinned_source_integration_when_submodule_checked_out(self):
        parser = Path(__file__).resolve().parents[1] / 'upstream/narou.rs/src/downloader/preprocess/parser.rs'
        if not parser.exists():
            self.skipTest('upstream submodule not checked out')
        content = parser.read_text()
        fixed = rewritten_source(content)
        self.assertIn(MARKER, fixed)
        self.assertTrue(fixed.startswith(content[:content.index(ENTRY)]))
        self.assertEqual(PINNED_UPSTREAM, "47bee6ba703441d3aa989e29694e3df485c4c643")
        self.assertEqual(EXPECTED_PARSER_BLOB, "41d61b8351ec7518bcdf1fda3e8c9be966260942")

if __name__ == '__main__':
    unittest.main()
