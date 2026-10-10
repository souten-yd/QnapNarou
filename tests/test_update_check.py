import unittest

from tools.update_check import validate_release


class UpdateCheckTests(unittest.TestCase):
    def release(self, tag="v0.2.0", name="QnapNarou_x86_64_0.2.0.qpkg"):
        return {"draft": False, "prerelease": False, "tag_name": tag,
                "assets": [{"name": name, "size": 5000, "digest": "sha256:" + ("a" * 64),
                            "browser_download_url": "https://github.com/souten-yd/QnapNarou/releases/download/" + tag + "/" + name}]}

    def test_available(self):
        info = validate_release(self.release(), "0.1.0", "x86_64")
        self.assertTrue(info["update_available"])

    def test_no_downgrade(self):
        info = validate_release(self.release(), "0.3.0", "x86_64")
        self.assertFalse(info["update_available"])

    def test_no_wrong_arch(self):
        with self.assertRaises(ValueError):
            validate_release(self.release(), "0.1.0", "arm_64")

    def test_reject_missing_digest(self):
        doc = self.release()
        del doc["assets"][0]["digest"]
        with self.assertRaises(ValueError):
            validate_release(doc, "0.1.0", "x86_64")

    def test_reject_other_origin(self):
        doc = self.release()
        doc["assets"][0]["browser_download_url"] = "https://example.org/payload.qpkg"
        with self.assertRaises(ValueError):
            validate_release(doc, "0.1.0", "x86_64")

    def test_reject_prerelease(self):
        doc = self.release()
        doc["prerelease"] = True
        with self.assertRaises(ValueError):
            validate_release(doc, "0.1.0", "x86_64")


if __name__ == "__main__":
    unittest.main()
