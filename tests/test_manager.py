import os
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from tools.manager import permitted_peer, html_page, narou_health, Handler


class FakeRequest:
    path = "/api/install"
    def __init__(self, nonce="sample-nonce", origin="http://qnap.local:8889"):
        self.result = None
        self.headers = {"Host": "qnap.local:8889", "Origin": origin,
                        "Content-Length": "0", "X-QN-Nonce": nonce}
        self.server = SimpleNamespace(csrf="sample-nonce")
    def allowed(self):
        return True
    def respond(self, status, body):
        self.result = status, body


class ManagerTests(unittest.TestCase):
    def test_private_and_tailscale(self):
        for address in ("127.0.0.1", "192.168.1.10", "10.1.2.3", "100.101.102.103"):
            self.assertTrue(permitted_peer(address), address)

    def test_public_peer_rejected(self):
        for address in ("8.8.8.8", "1.1.1.1", "invalid"):
            self.assertFalse(permitted_peer(address), address)

    def test_health_probe_is_read_only_and_offline(self):
        self.assertFalse(narou_health(port=1)["narou_running"])

    def test_portal_retains_upstream_and_installer_controls(self):
        page = html_page("test-nonce")
        for expected in (":8888/", "X-QN-Nonce", "/api/health", "/api/check",
                         "/api/install", "release-link", "QPKGを手動取得"):
            self.assertIn(expected, page)
        self.assertIn("'\\n'", page)
        self.assertIn("'\\n新しいQPKG", page)
        self.assertIn("j.auto_install_allowed && j.update_available", page)

    def test_invalid_nonce_and_cross_origin_rejected(self):
        for req in (FakeRequest(nonce="wrong"), FakeRequest(origin="http://evil.test")):
            Handler.do_POST(req)
            self.assertEqual(req.result[0], 403)

    def test_valid_web_request_spawns_only_stable_update_worker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            valid_release = {"current_version": "0.1.4", "latest_version": "v0.1.5",
                             "update_available": True, "auto_install_allowed": True}
            req = FakeRequest()
            with patch("tools.manager.LOCK_FILE", root / "update.lock"), \
                 patch("tools.manager.STATUS_FILE", root / "status.json"), \
                 patch("tools.manager.current_version", return_value="0.1.4"), \
                 patch("tools.manager.architecture", return_value="x86_64"), \
                 patch("tools.manager.fetch_releases", return_value=[]), \
                 patch("tools.manager.summarize_releases", return_value=valid_release), \
                 patch("tools.manager.write_status") as status, \
                 patch("tools.manager.subprocess.Popen", return_value=SimpleNamespace(pid=321)) as popen, \
                 patch.dict(os.environ, {"NAROU_DATA": tmp}):
                Handler.do_POST(req)
            self.assertEqual(req.result[0], 202)
            status.assert_called_once()
            popen.assert_called_once()
            argv = popen.call_args.args[0]
            self.assertEqual(argv[2:4], ["--current", "0.1.4"])
            self.assertIn(str(root / "updates"), argv)

    def test_busy_worker_and_preview_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "status.json").write_text('{"phase":"downloading"}')
            req = FakeRequest()
            with patch("tools.manager.LOCK_FILE", root / "update.lock"), \
                 patch("tools.manager.STATUS_FILE", root / "status.json"):
                Handler.do_POST(req)
            self.assertEqual(req.result[0], 409)
            (root / "status.json").unlink()
            req = FakeRequest()
            with patch("tools.manager.LOCK_FILE", root / "update.lock"), \
                 patch("tools.manager.STATUS_FILE", root / "status.json"), \
                 patch("tools.manager.current_version", return_value="0.1.4"), \
                 patch("tools.manager.architecture", return_value="x86_64"), \
                 patch("tools.manager.fetch_releases", return_value=[]), \
                 patch("tools.manager.summarize_releases", return_value={
                     "update_available": True, "auto_install_allowed": False}):
                Handler.do_POST(req)
            self.assertEqual(req.result[0], 409)


if __name__ == "__main__":
    unittest.main()
