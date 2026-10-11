"""QTS reboot regression: mimic a late-mounted QPKG and delayed Python.

Tests run against a copied shell script with isolated paths and local ephemeral
ports. Never require root, a real QNAP, disks, or live credentials.
"""
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest

BASE = Path(__file__).resolve().parents[1] / "qdk/shared/QnapNarou.sh"


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class QtsBootTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.install = self.root / "QnapNarou"
        self.install.mkdir()
        (self.install / "runtime").mkdir()
        self.volume = self.root / "install-path"
        self.volume.write_text("")
        self.backend_port = free_port()
        self.manager_port = free_port()
        self.assertNotEqual(self.backend_port, self.manager_port)
        getcfg = self.root / "getcfg"
        getcfg.write_text('#!/bin/sh\ncat "$TEST_INSTALL_FILE"\n')
        getcfg.chmod(0o755)

        socket_app = r'''#!/usr/bin/env python3
import socket, sys
if sys.argv[1] != "web" and sys.argv[1] != "--port":
    sys.exit(0)
port = int(sys.argv[sys.argv.index("--port") + 1])
server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("127.0.0.1", port))
server.listen(8)
while True:
    connection, addr = server.accept()
    connection.close()
'''
        # The script paths remain visible in /proc/pid/cmdline, allowing real
        # is_running() to detect the test processes and stop them cleanly.
        binfile = self.install / "runtime/narou_rs"
        binfile.write_text(socket_app)
        binfile.chmod(0o755)
        (self.install / "manager.py").write_text(socket_app)
        for f in ("installer.py", "update_check.py", "configure_hosts.py"):
            (self.install / f).write_text("import sys\n")
        ws = self.install / "ensure_ws.sh"
        ws.write_text("#!/bin/sh\nexit 0\n")
        ws.chmod(0o755)

        script = BASE.read_text()
        for original, new in (
            ("/sbin/getcfg", str(getcfg)),
            ("PIDFILE=/var/run/qpkg-narou.pid", f"PIDFILE={self.root}/narou.pid"),
            ("MANAGER_PIDFILE=/var/run/qpkg-narou-manager.pid",
             f"MANAGER_PIDFILE={self.root}/manager.pid"),
            ("BOOT_DIR=/var/run/qpkg-narou-boot-retry", f"BOOT_DIR={self.root}/boot-retry"),
            ("BOOT_REPORT=/var/run/qpkg-narou-boot-status", f"BOOT_REPORT={self.root}/boot-report"),
            ("BOOT_STOP=/var/run/qpkg-narou-boot-stop", f"BOOT_STOP={self.root}/boot-stop"),
            ("MANAGER_PORT=8889", f"MANAGER_PORT={self.manager_port}"),
            ("for candidate in /opt/bin/python3.11 /opt/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do",
             f"for candidate in {sys.executable}; do"),
            ('[ "$count" -lt 24 ]', '[ "$count" -lt 12 ]'),
            ('sleep 5', 'sleep 0.2'),
            ('sleep 2', 'sleep 0.2'),
        ):
            self.assertIn(original, script)
            script = script.replace(original, new)
        self.service = self.root / "QnapNarou.sh"
        self.service.write_text(script)
        self.env = dict(os.environ, TEST_INSTALL_FILE=str(self.volume),
                        NAROU_PORT=str(self.backend_port))
        subprocess.run(["sh", "-n", str(self.service)], check=True)

    def tearDown(self):
        try:
            subprocess.run(["/bin/sh", str(self.service), "stop"],
                           env=self.env, timeout=12, capture_output=True)
        except (OSError, subprocess.TimeoutExpired):
            for name in ("narou.pid", "manager.pid", "boot-retry/pid"):
                pidfile = self.root / name
                if pidfile.exists():
                    try:
                        os.kill(int(pidfile.read_text().strip()), 15)
                    except (ProcessLookupError, ValueError):
                        pass

    def run_service(self, action, timeout=12):
        return subprocess.run(["/bin/sh", str(self.service), action],
                              env=self.env, capture_output=True, text=True,
                              timeout=timeout)

    def test_cold_boot_recovers_after_install_volume_appears(self):
        start = time.monotonic()
        first = self.run_service("start")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertLess(time.monotonic() - start, 2)
        self.assertIn("starting", self.run_service("status").stdout)

        self.volume.write_text(str(self.install))
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            result = self.run_service("status")
            if result.stdout.strip() == "running":
                break
            time.sleep(0.1)
        else:
            self.fail("cold boot never became healthy: " + self.run_service("status").stdout)
        self.assertIn("running", self.run_service("status").stdout)
        self.assertTrue((self.root / "boot-report").exists())

    def test_stop_cancels_pending_boot_and_never_starts_late(self):
        self.assertEqual(self.run_service("start").returncode, 0)
        self.assertEqual(self.run_service("stop").returncode, 0)
        self.volume.write_text(str(self.install))
        time.sleep(0.6)
        self.assertNotEqual(self.run_service("status").returncode, 0)
        self.assertFalse((self.root / "narou.pid").exists())
        self.assertFalse((self.root / "manager.pid").exists())

    def test_service_has_no_legacy_startup_one_second_abort(self):
        source = BASE.read_text()
        self.assertNotIn('[ -n "$PYTHON" ] || { echo', source)
        self.assertIn("waiting for Python 3 /opt readiness", source)
        self.assertIn("startup timed out", source)
        self.assertIn("ports_ready", source)
        self.assertIn("BOOT_STOP", source)
        self.assertNotIn("rm -rf \"$LIBRARY\"", source)


if __name__ == "__main__":
    unittest.main()
