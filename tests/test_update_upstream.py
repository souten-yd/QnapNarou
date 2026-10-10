import unittest
from pathlib import Path
from unittest.mock import patch

from tools.update_upstream import update


class UpstreamSyncTests(unittest.TestCase):
    @patch("tools.update_upstream.require_clean")
    @patch("tools.update_upstream.git")
    @patch("tools.update_upstream.SUBMODULE")
    def test_dry_run_never_checkout(self, submodule, git, clean):
        submodule.__truediv__.return_value.exists.return_value = True
        git.side_effect = [type("Result", (), {"stdout": "a" * 40})(),
                           type("Result", (), {"stdout": ""})(),
                           type("Result", (), {"stdout": "b" * 40})(),
                           type("Result", (), {"returncode": 0})(),
                           type("Result", (), {"stdout": "commit"})()]
        self.assertTrue(update())
        self.assertFalse(any("checkout" in c.args for c in git.call_args_list))

    @patch("tools.update_upstream.require_clean")
    @patch("tools.update_upstream.git")
    @patch("tools.update_upstream.SUBMODULE")
    def test_apply_requires_exact_reviewed_sha(self, submodule, git, clean):
        submodule.__truediv__.return_value.exists.return_value = True
        git.side_effect = [type("Result", (), {"stdout": "a" * 40})(),
                           type("Result", (), {"stdout": ""})(),
                           type("Result", (), {"stdout": "b" * 40})(),
                           type("Result", (), {"returncode": 0})(),
                           type("Result", (), {"stdout": "commit"})()]
        with self.assertRaises(ValueError):
            update(apply=True, target="c" * 40)


if __name__ == "__main__":
    unittest.main()
