import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.installer import plan, download_package, apply_update


def release(version):
    name = "QnapNarou_x86_64_" + version + ".qpkg"
    return {"tag_name": "v" + version, "draft": False, "prerelease": False,
            "assets": [{"name": name, "digest": "sha256:" + ("a" * 64), "size": 5000,
                        "browser_download_url": "https://github.com/souten-yd/QnapNarou/releases/download/v" +
                        version + "/" + name}]}


class InstallerTests(unittest.TestCase):
    def test_requires_rollback_package(self):
        with self.assertRaises(ValueError):
            plan("0.1.0", "x86_64", release("0.2.0"), release("0.3.0"))

    def test_plan_accepts_upgrade(self):
        old, new = plan("0.1.0", "x86_64", release("0.2.0"), release("0.1.0"))
        self.assertFalse(old["update_available"])
        self.assertTrue(new["update_available"])

    def test_reject_corrupt_download(self):
        payload = b"x" * 5000
        doc = release("0.2.0")
        from tools.update_check import validate_release
        info = validate_release(doc, "0.1.0", "x86_64")
        class FakeResponse:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def geturl(self): return info["download_url"]
            def read(self, n): return payload[:n] if not hasattr(self, "done") else b""
        # Avoid test network access, exercise size/hash and cleanup.
        class Response(FakeResponse):
            def read(self, n):
                if getattr(self, "done", False): return b""
                self.done = True
                return payload
        with tempfile.TemporaryDirectory() as d:
            dest = Path(d) / "pkg.qpkg"
            with self.assertRaises(ValueError):
                download_package(info, dest, open_url=lambda *a, **k: Response())
            self.assertFalse(dest.exists())

    @patch("tools.installer.write_status")
    def test_rollback_on_install_failure(self, status):
        old = release("0.1.0")
        new = release("0.2.0")
        invocations = []
        def run(command, **kwargs):
            invocations.append(command)
            if len(invocations) == 1:
                raise RuntimeError("installation error")
        def dl(info, dest):
            dest.write_bytes(b"dummy")
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(RuntimeError, "previous version restored"):
                apply_update("0.1.0", "x86_64", Path(d), run_command=run,
                             fetch=lambda tag=None: new if tag is None else old, download=dl)
            self.assertEqual(len(invocations), 2)
            self.assertFalse(list(Path(d).glob("*.qpkg")))


if __name__ == "__main__":
    unittest.main()
