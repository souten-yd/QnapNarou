import unittest
from unittest.mock import patch
from tools.update_upstream import sync


class UpstreamSyncTests(unittest.TestCase):
    def test_tag_not_branch(self):
        with self.assertRaises(ValueError):
            sync("main")

    def test_apply_requires_exact_sha(self):
        with self.assertRaises(ValueError):
            sync("v0.5.3", apply=True)

    @patch("tools.update_upstream.git")
    @patch("tools.update_upstream.UPSTREAM")
    def test_dry_run_never_checkouts_or_stages(self, upstream, git):
        upstream.__truediv__.return_value.exists.return_value = True
        def result(*args, **kwargs):
            if args[-1] in ("HEAD", ":upstream/narou.rs"):
                out = "a" * 40
            elif "refs/tags/" in args[-1]:
                out = "b" * 40
            else:
                out = ""
            return type("GitResult", (), {"stdout": out, "returncode": 0})()
        git.side_effect = result
        self.assertTrue(sync("v0.5.3"))
        self.assertFalse(any("checkout" in c.args or "add" in c.args for c in git.call_args_list))


if __name__ == "__main__":
    unittest.main()
