import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "qdk/shared/ensure_ws.sh"


class EnsureWsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.value = self.root / "setting"
        self.bin = self.root / "narou_rs"
        self.bin.write_text("""#!/bin/sh
case "$1" in
  setting)
    case "$2" in
      server-ws-port) cat "$MOCK_WS_SETTING" ;;
      server-ws-port=0) printf 0 >"$MOCK_WS_SETTING" ;;
      *) exit 2 ;;
    esac ;;
  *) exit 2 ;;
esac
""")
        self.bin.chmod(0o755)

    def execute(self):
        return subprocess.run(["sh", str(SCRIPT), str(self.bin), "8889"], 
                              env={**os.environ, "MOCK_WS_SETTING": str(self.value)},
                              capture_output=True, text=True)

    def test_unset_websocket_uses_shared_http_port(self):
        self.value.write_text("")
        result = self.execute()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.value.read_text(), "0")

    def test_previous_conflicting_8889_is_repaired(self):
        self.value.write_text("8889")
        self.assertEqual(self.execute().returncode, 0)
        self.assertEqual(self.value.read_text(), "0")

    def test_existing_shared_port_remains_unchanged(self):
        self.value.write_text("0")
        self.assertEqual(self.execute().returncode, 0)
        self.assertEqual(self.value.read_text(), "0")

    def test_explicit_nonconflicting_port_preserved(self):
        self.value.write_text("8891")
        self.assertEqual(self.execute().returncode, 0)
        self.assertEqual(self.value.read_text(), "8891")

    def test_failure_does_not_claim_success(self):
        self.bin.write_text("#!/bin/sh\nexit 7\n")
        self.assertNotEqual(self.execute().returncode, 0)


if __name__ == "__main__":
    unittest.main()
