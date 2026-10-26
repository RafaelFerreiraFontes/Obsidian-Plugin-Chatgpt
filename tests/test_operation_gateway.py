import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SERVER_DIR = Path(__file__).resolve().parents[1] / "server"
sys.path.insert(0, str(SERVER_DIR))
spec = importlib.util.spec_from_file_location("operation_gateway", SERVER_DIR / "operation_gateway.py")
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


def call(name="bridge_status", **arguments):
    return {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
            "params": {"name": name, "arguments": arguments}}


class GatewayTests(unittest.TestCase):
    def test_discovery_does_not_spawn_worker(self):
        with patch.object(g, "worker_call") as worker:
            result = g.dispatch({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
            self.assertEqual(len(result["result"]["tools"]), 11)
            self.assertIsNone(g.dispatch({"jsonrpc": "2.0", "method": "notifications/initialized"}))
            g.dispatch({"jsonrpc": "2.0", "id": 2, "method": "ping"})
            worker.assert_not_called()

    def test_real_worker_exits_before_response_and_reloads_revocation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vault = root / "vault"
            vault.mkdir()
            (vault / ".obsidian").mkdir()
            (vault / "sample.md").write_text("private content", encoding="utf-8")
            data = root / "ObsidianVaultBridge"
            data.mkdir()
            config = data / "grants.json"
            config.write_text(json.dumps({"v": {"path": str(vault), "read": True}}))
            with patch.dict(os.environ, {"LOCALAPPDATA": tmp}):
                status = g.worker_call(call())
                pid = json.loads(status["result"]["content"][0]["text"])["worker_pid"]
                # The run call must have returned only after wait/reap.
                if os.name == "nt":
                    import ctypes
                    handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
                    if handle:
                        try:
                            code = ctypes.c_ulong()
                            ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
                            self.assertNotEqual(code.value, 259)  # STILL_ACTIVE
                        finally:
                            ctypes.windll.kernel32.CloseHandle(handle)
                else:
                    with self.assertRaises(ProcessLookupError):
                        os.kill(pid, 0)
                listing = g.worker_call(call("list_notes", vault_id="v", limit=1))
                self.assertEqual(json.loads(listing["result"]["content"][0]["text"])["paths"], ["sample.md"])
                config.write_text("{}")
                self.assertTrue(g.worker_call(call("list_notes", vault_id="v"))["result"]["isError"])

    def test_credentials_are_not_forwarded_to_worker(self):
        result = subprocess.CompletedProcess([], 0, stdout=json.dumps({"jsonrpc": "2.0", "id": 4, "result": {}}))
        with patch.dict(os.environ, {"CONTROL_PLANE_API_KEY": "secret", "OPENAI_API_KEY": "other"}), \
                patch.object(g.subprocess, "run", return_value=result) as run:
            g.worker_call(call())
            self.assertNotIn("CONTROL_PLANE_API_KEY", run.call_args.kwargs["env"])
            self.assertNotIn("OPENAI_API_KEY", run.call_args.kwargs["env"])
            self.assertFalse(run.call_args.kwargs["shell"])

    def test_timeout_is_reported_without_payload_or_key(self):
        with patch.object(g, "worker_call", side_effect=subprocess.TimeoutExpired("secret", 1)):
            result = g.dispatch(call())
        self.assertTrue(result["result"]["isError"])
        self.assertNotIn("secret", json.dumps(result))

    def test_real_timeout_kills_and_reaps_worker(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "sleep.py"
            script.write_text("import time; time.sleep(10)")
            with patch.object(g, "WORKER", script), self.assertRaises(subprocess.TimeoutExpired):
                g.worker_call(call(), timeout=0.1)

    def test_malformed_worker_response_is_reported(self):
        with patch.object(g.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, stdout="bad")):
            self.assertTrue(g.dispatch(call())["result"]["isError"])

    def test_gateway_process_handles_two_operations(self):
        with tempfile.TemporaryDirectory() as tmp:
            messages = [call(), {"jsonrpc": "2.0", "id": 8, "method": "tools/list"}, call()]
            result = subprocess.run([sys.executable, str(SERVER_DIR / "operation_gateway.py")],
                                    input="\n".join(map(json.dumps, messages)) + "\n",
                                    capture_output=True, text=True, encoding="utf-8", timeout=15,
                                    env={**os.environ, "LOCALAPPDATA": tmp})
            self.assertEqual(result.returncode, 0, result.stderr)
            responses = [json.loads(line) for line in result.stdout.splitlines()]
            self.assertEqual(len(responses), 3)
            first = json.loads(responses[0]["result"]["content"][0]["text"])
            last = json.loads(responses[2]["result"]["content"][0]["text"])
            self.assertNotEqual(first["worker_pid"], last["worker_pid"])
            self.assertEqual(len(responses[1]["result"]["tools"]), 11)


if __name__ == "__main__":
    unittest.main()
