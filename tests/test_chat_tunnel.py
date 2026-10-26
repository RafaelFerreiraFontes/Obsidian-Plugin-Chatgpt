import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / "tools/chat_tunnel.py"
spec = importlib.util.spec_from_file_location("chat_tunnel", SCRIPT)
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
TEST_ID = "tunnel_" + "a" * 32  # Synthetic fixture; never submitted to OpenAI.
TEST_APP = "asdk_app_test_fixture"


class ChatTunnelTests(unittest.TestCase):
    def test_rejects_placeholder_and_url(self):
        for value in ["", "tunnel_REPLACE_ME", "https://localhost/mcp", TEST_ID + "x"]:
            with self.subTest(value=value), self.assertRaises(argparse.ArgumentTypeError):
                t.tunnel_id(value)

    def test_init_quotes_paths_with_spaces(self):
        argv = t.client_command("init", TEST_ID, python="C:/Program Files/Python/python.exe")
        self.assertEqual(argv[-2], "--mcp-command")
        self.assertTrue(argv[-1].startswith('"C:/Program Files/Python/python.exe" "'))
        self.assertIn("server/bridge.py", argv[-1])
        self.assertNotIn("CONTROL_PLANE_API_KEY", " ".join(argv))

    def test_doctor_and_run_share_profile(self):
        self.assertEqual(t.client_command("doctor"),
                         ["tunnel-client", "doctor", "--profile", t.PROFILE, "--explain"])
        self.assertEqual(t.client_command("run"),
                         ["tunnel-client", "run", "--profile", t.PROFILE])

    def test_package_preserves_identity_and_excludes_local_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "chat.zip"
            original = (t.ROOT / "mcp.json").read_bytes()
            t.package(TEST_ID, output, TEST_APP)
            with zipfile.ZipFile(output) as z:
                self.assertIsNone(z.testzip())
                self.assertEqual(set(z.namelist()), {"plugin.json", "mcp.json", ".app.json", "assets/icon.svg",
                                                   "skills/obsidian-vault/SKILL.md"})
                manifest = json.loads(z.read("plugin.json"))
                source = json.loads((t.ROOT / "plugin.json").read_text(encoding="utf-8-sig"))
                self.assertEqual(manifest["name"], source["name"])
                self.assertEqual(manifest["extensions"]["com.openai"]["interface"],
                                 source["extensions"]["com.openai"]["interface"])
                self.assertFalse(manifest["extensions"]["com.openai"]["requires_local_executor"])
                self.assertEqual(manifest["extensions"]["com.openai"]["apps"], "./.app.json")
                self.assertEqual(json.loads(z.read(".app.json"))["apps"]["obsidian-vault-bridge"]["id"], TEST_APP)
                server = json.loads(z.read("mcp.json"))["mcpServers"]["obsidian-vault-bridge"]
                self.assertEqual(server["type"], "streamable-http")
                self.assertEqual(server["extensions"]["com.openai"]["tunnelId"], TEST_ID)
                self.assertNotIn("url", server)
                self.assertNotIn("command", server)
            self.assertEqual((t.ROOT / "mcp.json").read_bytes(), original)
            with self.assertRaises(FileExistsError):
                t.package(TEST_ID, output, TEST_APP)

    def test_package_cannot_pollute_source_directory(self):
        with self.assertRaises(ValueError):
            t.package(TEST_ID, t.ROOT / "generated.zip", TEST_APP)

    def test_package_requires_registered_app(self):
        for app in [None, "plugin_asdk_app_fixture", "https://example.com", "asdk_app_../bad"]:
            with self.subTest(app=app), self.assertRaises(ValueError):
                t.package(TEST_ID, t.ROOT.parent / "unused.zip", app)

    def test_missing_tunnel_is_not_treated_as_connected(self):
        r = subprocess.run([sys.executable, str(SCRIPT), "init"], capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--tunnel-id", r.stderr)

    def test_preflight_does_not_disclose_key(self):
        from contextlib import redirect_stdout
        import io
        out = io.StringIO()
        with patch.object(sys, "argv", [str(SCRIPT), "check"]), \
                patch.dict(t.os.environ, {"CONTROL_PLANE_API_KEY": "test-secret"}), \
                patch.object(t.shutil, "which", return_value=None), redirect_stdout(out):
            self.assertEqual(t.main(), 2)
        self.assertNotIn("test-secret", out.getvalue())
        self.assertFalse(json.loads(out.getvalue())["chat_access_verified"])


if __name__ == "__main__":
    unittest.main()
