import unittest
from tools.update_check import summarize_releases, validate_release, parse_version


def release(version, *, rc=None, arch="x86_64", digest=True, draft=False):
    tag = f"v{version}" + (f"-rc{rc}" if rc is not None else "")
    asset = {"name": f"QnapNarou_{arch}_{version}.qpkg",
             "size": 31457280,
             "browser_download_url": (
                 "https://github.com/souten-yd/QnapNarou/releases/download/"
                 + tag + f"/QnapNarou_{arch}_{version}.qpkg")}
    if digest:
        asset["digest"] = "sha256:" + "f" * 64
    return {"tag_name": tag, "prerelease": rc is not None,
            "draft": draft, "published_at": "2026-10-10T16:14:36Z",
            "assets": [asset]}


class ReleaseDiscoveryTests(unittest.TestCase):
    def test_preview_only_returns_rc3_not_http_404(self):
        versions = [release("0.1.0", rc=1), release("0.1.1", rc=2),
                    release("0.1.2", rc=3)]
        result = summarize_releases(versions, "0.1.1", "x86_64")
        self.assertEqual(result["latest_version"], "v0.1.2-rc3")
        self.assertTrue(result["update_available"])
        self.assertTrue(result["prerelease"])
        self.assertFalse(result["auto_install_allowed"])
        self.assertTrue(result["download_url"].endswith("/QnapNarou_x86_64_0.1.2.qpkg"))

    def test_existing_rc3_is_not_newer_than_itself(self):
        result = summarize_releases([release("0.1.2", rc=3)],
                                    "0.1.2", "x86_64")
        self.assertFalse(result["update_available"])
        self.assertEqual(result["latest_version"], "v0.1.2-rc3")

    def test_prefers_stable_over_rc_at_same_version(self):
        result = summarize_releases([release("0.2.0", rc=4),
                                     release("0.2.0")], "0.1.2", "x86_64")
        self.assertEqual(result["latest_version"], "v0.2.0")
        self.assertFalse(result["prerelease"])

    def test_newer_rc_beats_older_stable(self):
        result = summarize_releases([release("0.2.0"),
                                     release("0.3.0", rc=1)], "0.1.2", "x86_64")
        self.assertEqual(result["latest_version"], "v0.3.0-rc1")

    def test_ignores_drafts_and_wrong_arch(self):
        result = summarize_releases([release("0.9.0", draft=True),
                                     release("0.8.0", arch="arm_64"),
                                     release("0.1.1", rc=2)], "0.1.0", "x86_64")
        self.assertEqual(result["latest_version"], "v0.1.1-rc2")

    def test_rejects_missing_digest_or_untrusted_url(self):
        unsafe = release("0.1.3", rc=4, digest=False)
        good = release("0.1.2", rc=3)
        self.assertEqual(summarize_releases([unsafe, good], "0.1.1", "x86_64")["latest_version"],
                         "v0.1.2-rc3")
        unsafe = release("0.1.3", rc=4)
        unsafe["assets"][0]["browser_download_url"] = "https://other.example/bad.qpkg"
        self.assertEqual(summarize_releases([unsafe, good], "0.1.1", "x86_64")["latest_version"],
                         "v0.1.2-rc3")

    def test_wrong_channel_and_invalid_rc_not_selected(self):
        x = release("0.1.3", rc=4)
        x["prerelease"] = False
        self.assertIsNone(summarize_releases([x], "0.1.2", "x86_64")["latest_version"])
        with self.assertRaises(ValueError):
            validate_release(x, "0.1.2", "x86_64", allow_prerelease=True)

    def test_no_releases_is_nonexceptional(self):
        d = summarize_releases([], "0.1.2", "x86_64")
        self.assertIsNone(d["latest_version"])
        self.assertFalse(d["auto_install_allowed"])

    def test_legacy_auto_install_policy_rejects_preview(self):
        with self.assertRaisesRegex(ValueError, "stable"):
            validate_release(release("0.1.3", rc=4), "0.1.2", "x86_64")

    def test_reject_unknown_or_malformed_version(self):
        with self.assertRaises(ValueError):
            parse_version("0.1.3-rc4")


if __name__ == "__main__":
    unittest.main()
