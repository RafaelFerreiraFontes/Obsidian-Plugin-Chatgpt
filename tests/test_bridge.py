import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SERVER = Path(__file__).resolve().parents[1] / "server" / "bridge.py"
spec = importlib.util.spec_from_file_location("bridge", SERVER)
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get("BRIDGE_TEST_TMP"))
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / "Vault"
        self.root.mkdir()
        (self.root / ".obsidian").mkdir()
        self.patches = [patch.object(b, "DATA", self.base / "data"),
                        patch.object(b, "CONFIG", self.base / "data" / "grants.json")]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)
        b.atomic_json(b.CONFIG, {"v": {"path": str(self.root), "read": True, "write": True, "cli": True}})

    def test_create_read_and_cite_unicode(self):
        r = b.write_note("v", "Nota á.md", "Título\nlinha dois\n", "new")
        read = b.read_note("v", "Nota á.md", 2, 2)
        self.assertEqual(read["sha256"], r["sha256"])
        self.assertEqual(read["text"], "2: linha dois")
        self.assertTrue(read["uri"].startswith("obsidian://open?path="))
        self.assertEqual(read["citation"], "Nota á.md:L2-L2")

    def test_backup_and_conflict(self):
        old = b.write_note("v", "a.md", "original", "new")
        new = b.write_note("v", "a.md", "updated", old["sha256"])
        self.assertEqual(Path(new["backup"]).read_text(), "original")
        with self.assertRaises(ValueError):
            b.write_note("v", "a.md", "stale", old["sha256"])
        self.assertEqual((self.root / "a.md").read_text(), "updated")
        with self.assertRaises(ValueError):
            b.write_note("v", "a.md", "overwrite", "new")

    def test_empty_file_and_invalid_citation_range(self):
        b.write_note("v", "empty.md", "", "new")
        self.assertEqual(b.read_note("v", "empty.md")["citation"], "empty.md (arquivo vazio)")
        with self.assertRaises(ValueError):
            b.read_note("v", "empty.md", 2, 5)

    def test_external_edit_conflicts(self):
        old = b.write_note("v", "a.md", "original", "new")
        (self.root / "a.md").write_text("external", encoding="utf-8")
        with self.assertRaises(ValueError):
            b.write_note("v", "a.md", "lost update", old["sha256"])

    def test_invalid_paths(self):
        for path in ["../outside.md", "/a.md", "C:/a.md", "a\\b.md", ".obsidian/secret.md",
                     "sub/../a.md", "a.md:stream", "a.py", "CON.md", "x./a.md", "a//b.md"]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                b.safe_path(self.root, path)

    def test_hardlinks_denied(self):
        target = self.base / "outside.md"
        target.write_text("secret")
        os.link(target, self.root / "link.md")
        with self.assertRaises(ValueError):
            b.read_note("v", "link.md")

    def test_symlink_denied(self):
        target = self.base / "outside.md"
        target.write_text("secret")
        try:
            (self.root / "link.md").symlink_to(target)
        except OSError:
            self.skipTest("Windows does not permit symlink creation in this session")
        with self.assertRaises(ValueError):
            b.read_note("v", "link.md")

    @unittest.skipUnless(os.name == "nt", "Windows junction test")
    def test_windows_junction_denied(self):
        target = self.base / "outside"
        target.mkdir()
        (target / "secret.md").write_text("secret")
        junction = self.root / "junction"
        # Test-only junction setup, fixed program and arguments, no user input.
        result = subprocess.run(["cmd.exe", "/c", "mklink", "/J", str(junction), str(target)], capture_output=True)
        if result.returncode:
            self.skipTest("Junction creation unavailable")
        with self.assertRaises(ValueError):
            b.read_note("v", "junction/secret.md")
        self.assertNotIn("junction/secret.md", b.list_notes("v")["paths"])

    def test_read_only_and_revoke(self):
        g = b.grants()
        g["v"]["write"] = False
        b.atomic_json(b.CONFIG, g)
        with self.assertRaises(PermissionError):
            b.write_note("v", "a.md", "blocked", "new")
        b.revoke_vault("v")
        with self.assertRaises(PermissionError):
            b.list_notes("v")

    def test_hidden_files_and_pagination(self):
        for name in ["a.md", "b.base", "c.md", ".hidden.md"]:
            (self.root / name).write_text("hello", encoding="utf-8")
        (self.root / ".obsidian" / "secret.md").write_text("secret")
        first = b.list_notes("v", limit=2)
        second = b.list_notes("v", offset=first["next_offset"], limit=2)
        self.assertEqual(first["paths"] + second["paths"], ["a.md", "b.base", "c.md"])

    def test_search_and_limits(self):
        b.write_note("v", "a.md", "AÇÃO\nAção\n", "new")
        result = b.search_notes("v", "ação", limit=1)
        self.assertEqual(len(result["matches"]), 1)
        self.assertTrue(result["truncated"])
        (self.root / "large.md").write_bytes(b"x" * (b.MAX_BYTES + 1))
        with self.assertRaises(ValueError):
            b.read_note("v", "large.md")
        self.assertEqual(b.search_notes("v", "ação")["skipped"], 1)

    def test_base_formula_is_data(self):
        expression = 'if(price > 0, price * quantity, 0)'
        b.create_formula_base("v", "Total.base", "total", expression)
        obj = json.loads((self.root / "Total.base").read_text(encoding="utf-8"))
        self.assertEqual(obj["formulas"]["total"], expression)
        with self.assertRaises(ValueError):
            b.create_formula_base("v", "Total.base", "total", "0")

    def test_schema_validation(self):
        msg = {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {
            "name": "list_notes", "arguments": {"vault_id": "v", "limit": True}}}
        self.assertTrue(b.dispatch(msg)["result"]["isError"])
        msg["params"]["arguments"] = {"vault_id": "v", "unexpected": "x"}
        self.assertTrue(b.dispatch(msg)["result"]["isError"])

    def test_wrong_cli_vault_refused(self):
        with patch.object(b, "cli_run", return_value=str(self.base / "Other")):
            with self.assertRaises(PermissionError):
                b.obsidian_query("v", "plugins")

    def test_cli_has_no_shell_and_fixed_arguments(self):
        completed = subprocess.CompletedProcess([], 0, stdout="ok", stderr="")
        with patch.object(b, "cli_executable", return_value="obsidian"), patch.object(b.subprocess, "run", return_value=completed) as run:
            b.cli_run(self.root, ["command", "id=abc"])
            self.assertFalse(run.call_args.kwargs["shell"])
            self.assertEqual(run.call_args.args[0], ["obsidian", "command", "id=abc"])

    def test_plugin_action_requires_local_confirmation(self):
        with patch.object(b, "checked_cli", return_value=self.root), patch.object(b, "native_dialog", return_value=False), patch.object(b, "cli_run") as run:
            self.assertTrue(b.plugin_action("v", "install", "test-plugin")["cancelled"])
            run.assert_not_called()
        with patch.object(b, "checked_cli", return_value=self.root), patch.object(b, "native_dialog", return_value=True), patch.object(b, "cli_run", return_value="installed") as run:
            b.plugin_action("v", "install", "test-plugin")
            self.assertEqual(run.call_args.args[1], ["plugin:install", "id=test-plugin"])

    def test_stdio_discovery_and_harmless_status(self):
        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "bridge_status", "arguments": {}}},
        ]
        env = {**os.environ, "LOCALAPPDATA": str(self.base / "isolated")}
        result = subprocess.run([sys.executable, str(SERVER)], input="\n".join(map(json.dumps, requests)) + "\n", text=True, encoding="utf-8", capture_output=True, timeout=15, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        messages = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(len(messages), 3)
        self.assertEqual(len(messages[1]["result"]["tools"]), 11)
        self.assertFalse(messages[2]["result"]["isError"])
        status = json.loads(messages[2]["result"]["content"][0]["text"])
        self.assertEqual(status["vaults"], {})


if __name__ == "__main__":
    unittest.main(verbosity=2)
