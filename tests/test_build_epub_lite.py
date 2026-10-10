import unittest
from tools.build_epub_lite import (corrected_web_source, corrected_download_ui, START, END,
                                  DOWNLOAD_ANCHOR, FIXED_DOWNLOAD_ANCHOR)


class EpubLiteBuildTests(unittest.TestCase):
    def sample(self):
        return (
            '#[cfg(feature = "lite")]\nasync fn generate_epub_on_demand() {\n'
            + START + '\n'
            + '    SELECT payload FROM novel_outputs;\n'
            + '    return Ok((payload, filename));\n'
            + '    }\n'
            + END + '\n'
            + '    build_book_from_text();\n'
            + '}\n'
        )

    def test_replaces_raw_text_ebook_response(self):
        fixed = corrected_web_source(self.sample())
        self.assertNotIn('return Ok((payload, filename));', fixed)
        self.assertIn('build_book_from_text();', fixed)
        self.assertIn('Aozora TEXT, not an EPUB', fixed)

    def test_rejects_moved_or_changed_fast_path(self):
        with self.assertRaises(ValueError):
            corrected_web_source(self.sample().replace('novel_outputs', 'another_table'))

    def test_idempotence_guard(self):
        with self.assertRaises(ValueError):
            corrected_web_source(corrected_web_source(self.sample()))

    def test_qnap_safari_download_keeps_original_novel_list(self):
        source = ('const downloadLink = `<a href="/novels/${encodeURIComponent(String(novel.id))}/download" '
                  + DOWNLOAD_ANCHOR + '>↓</a>`;')
        result = corrected_download_ui(source)
        self.assertIn(FIXED_DOWNLOAD_ANCHOR, result)
        self.assertIn('download target="_blank" rel="noopener noreferrer"', result)
        self.assertIn('/novels/${encodeURIComponent(String(novel.id))}/download', result)
        self.assertEqual(result.count("btn-download"), 1)

    def test_qnap_safari_patch_rejects_upstream_drift(self):
        sample = '<a href="/novels/1/download" ' + DOWNLOAD_ANCHOR + '>↓</a>'
        with self.assertRaises(ValueError):
            corrected_download_ui(sample)
        with self.assertRaises(ValueError):
            corrected_download_ui("no download link")

    def test_qnap_safari_patch_cannot_double_apply(self):
        sample = ('<a href="/novels/${encodeURIComponent(String(novel.id))}/download" '
                  + DOWNLOAD_ANCHOR + '>↓</a>')
        with self.assertRaises(ValueError):
            corrected_download_ui(corrected_download_ui(sample))

    def test_pinned_upstream_ui_integration_if_checked_out(self):
        from pathlib import Path
        source = (Path(__file__).resolve().parents[1] /
                  "upstream/narou.rs/src/web/assets/js/ui/render.js")
        if not source.is_file():
            self.skipTest("upstream submodule not checked out")
        patched = corrected_download_ui(source.read_text(encoding="utf-8"))
        self.assertIn(FIXED_DOWNLOAD_ANCHOR, patched)
        self.assertEqual(patched.count(FIXED_DOWNLOAD_ANCHOR), 1)

    def test_no_lite_feature_rejected(self):
        with self.assertRaises(ValueError):
            corrected_web_source(self.sample().replace('#[cfg(feature = "lite")]', '#[cfg(not(feature = "lite"))]'))


if __name__ == "__main__":
    unittest.main()
