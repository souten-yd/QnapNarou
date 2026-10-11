import unittest
from tools.build_epub_lite import (corrected_web_source, corrected_download_ui, START, END,
                                  DOWNLOAD_ANCHOR, FIXED_DOWNLOAD_ANCHOR, OVERLAY_MARKER, DOWNLOAD_ROUTE)


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

    def download_fixture(self):
        return ('const downloadLink = "<a href=\\"/novels/${encodeURIComponent(String(novel.id))}/download\\" "'
                + DOWNLOAD_ANCHOR + '">DL</a>";')

    def test_qnap_epub_overlay_preserves_original_page(self):
        fixed = corrected_download_ui(self.download_fixture())
        self.assertIn(FIXED_DOWNLOAD_ANCHOR, fixed)
        self.assertIn(OVERLAY_MARKER, fixed)
        self.assertIn("event.preventDefault()", fixed)
        self.assertIn("event.stopImmediatePropagation()", fixed)
        self.assertIn("navigator.share", fixed)
        self.assertIn("URL.createObjectURL", fixed)
        self.assertIn("link.target = '_blank'", fixed)
        self.assertNotIn('download target="_blank"', fixed)
        self.assertEqual(fixed.count(FIXED_DOWNLOAD_ANCHOR), 1)

    def test_qnap_overlay_is_idempotence_guarded(self):
        first = corrected_download_ui(self.download_fixture())
        with self.assertRaises(ValueError):
            corrected_download_ui(first)

    def test_qnap_overlay_fails_when_upstream_link_changes(self):
        bad = self.download_fixture().replace(DOWNLOAD_ROUTE, "/other/api")
        with self.assertRaises(ValueError):
            corrected_download_ui(bad)
        with self.assertRaises(ValueError):
            corrected_download_ui("no anchor")
        with self.assertRaises(ValueError):
            corrected_download_ui(self.download_fixture() * 2)

    def test_qnap_overlay_fails_if_supporting_module_is_incomplete(self):
        with self.assertRaises(ValueError):
            corrected_download_ui(self.download_fixture(), "/* missing */")
        from tools.build_epub_lite import OVERLAY_PATH
        self.assertTrue(OVERLAY_PATH.is_file())

    def test_pinned_upstream_ui_integration_if_checked_out(self):
        from pathlib import Path
        source = (Path(__file__).resolve().parents[1] /
                  "upstream/narou.rs/src/web/assets/js/ui/render.js")
        if not source.is_file():
            self.skipTest("upstream submodule not checked out")
        patched = corrected_download_ui(source.read_text(encoding="utf-8"))
        self.assertIn(FIXED_DOWNLOAD_ANCHOR, patched)
        self.assertEqual(patched.count(OVERLAY_MARKER), 1)
        self.assertEqual(patched.count(FIXED_DOWNLOAD_ANCHOR), 1)

    def test_no_lite_feature_rejected(self):
        with self.assertRaises(ValueError):
            corrected_web_source(self.sample().replace('#[cfg(feature = "lite")]', '#[cfg(not(feature = "lite"))]'))


if __name__ == "__main__":
    unittest.main()
