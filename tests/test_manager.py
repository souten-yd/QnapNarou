import unittest
from tools.manager import permitted_peer, html_page, narou_health


class ManagerTests(unittest.TestCase):
    def test_private_and_tailscale(self):
        for address in ("127.0.0.1", "192.168.1.10", "10.1.2.3", "100.101.102.103"):
            self.assertTrue(permitted_peer(address), address)

    def test_public_peer_rejected(self):
        for address in ("8.8.8.8", "1.1.1.1", "invalid"):
            self.assertFalse(permitted_peer(address), address)

    def test_health_probe_is_read_only_and_offline(self):
        info = narou_health(port=1)
        self.assertFalse(info["narou_running"])
        self.assertEqual(info["port"], 1)

    def test_portal_retains_upstream_ui_link(self):
        page = html_page("test-nonce")
        self.assertIn(":8888/", page)
        self.assertIn("X-QN-Nonce", page)
        self.assertIn("/api/health", page)
        self.assertIn("test-nonce", page)
        self.assertIn("/api/check", page)
        self.assertIn("release-link", page)
        self.assertIn("QPKGを取得", page)
        # Python's triple-quoted template must not expand JS escapes to raw
        # newlines inside quoted JavaScript string literals.
        self.assertIn("'\\n'", page)
        self.assertIn("'\\n新しいQPKG", page)



if __name__ == "__main__":
    unittest.main()
