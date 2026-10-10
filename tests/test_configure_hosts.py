import subprocess
import unittest
from types import SimpleNamespace

from tools.configure_hosts import merged_allowlist, trusted_ipv4, configure


class ConfigureHostsTests(unittest.TestCase):
    def test_only_private_lan_and_tailscale_addresses(self):
        self.assertTrue(trusted_ipv4("192.168.68.57"))
        self.assertTrue(trusted_ipv4("100.101.102.103"))
        for address in ("8.8.8.8", "127.0.0.1", "169.254.3.4", "garbage"):
            self.assertFalse(trusted_ipv4(address))

    def test_preserves_user_custom_hosts_without_duplicates(self):
        self.assertEqual(
            merged_allowlist("nas.local,192.168.68.57", 
                             ["192.168.68.57", "100.101.102.103"]),
            "nas.local,192.168.68.57,100.101.102.103")

    def test_no_writes_if_config_already_matches(self):
        calls = []
        def run(cmd, **kwargs):
            calls.append(cmd)
            if len(cmd) == 3:
                return SimpleNamespace(stdout="192.168.68.57\n")
            raise AssertionError("unexpected config write")
        configure("/narou_rs", ["192.168.68.57"], runner=run)
        self.assertEqual(len(calls), 2)

    def test_writes_both_http_and_websocket_allow_lists(self):
        commands = []
        def run(cmd, **kwargs):
            commands.append(cmd)
            return SimpleNamespace(stdout="nas.local\n")
        configure("/narou_rs", ["192.168.68.57"], runner=run)
        self.assertEqual(len(commands), 4)
        self.assertIn("server-add-accepted-hosts=nas.local,192.168.68.57", commands[1])
        self.assertIn("server-ws-add-accepted-domains=nas.local,192.168.68.57", commands[3])

    def test_empty_interfaces_abort_without_writes(self):
        with self.assertRaises(RuntimeError):
            configure("/narou_rs", [], runner=lambda *a, **k: None)


if __name__ == "__main__":
    unittest.main()
