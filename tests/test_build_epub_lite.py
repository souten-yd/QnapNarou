import unittest
from tools.build_epub_lite import corrected_web_source, START, END


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

    def test_no_lite_feature_rejected(self):
        with self.assertRaises(ValueError):
            corrected_web_source(self.sample().replace('#[cfg(feature = "lite")]', '#[cfg(not(feature = "lite"))]'))


if __name__ == "__main__":
    unittest.main()
