"""Persistent MCP control channel; vault operations use short-lived workers."""
import json
import os
from pathlib import Path
import subprocess
import sys

import bridge

WORKER = Path(__file__).with_name("bridge.py")
WORKER_TIMEOUT = 110  # Leave room inside the tunnel's 120-second deadline.


def worker_call(message, timeout=WORKER_TIMEOUT):
    # The file worker never needs the tunnel or OpenAI API credentials.
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("CONTROL_PLANE_", "OPENAI_"))}
    result = subprocess.run(
        [sys.executable, str(WORKER)],
        input=json.dumps(message, ensure_ascii=False) + "\n",
        text=True, encoding="utf-8", capture_output=True, timeout=timeout,
        env=env, shell=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    # subprocess.run waits for and reaps the worker before returning its result.
    if result.returncode or len(result.stdout.encode("utf-8")) > bridge.MAX_BYTES * 8:
        raise RuntimeError("A operação local falhou; o subprocesso foi encerrado.")
    response = json.loads(result.stdout)
    if not isinstance(response, dict) or response.get("id") != message.get("id"):
        raise RuntimeError("Resposta inválida do subprocesso local.")
    return response


def dispatch(message):
    if (isinstance(message, dict) and message.get("jsonrpc") == "2.0"
            and message.get("method") == "tools/call" and "id" in message):
        try:
            return worker_call(message)
        except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
            error = ("Tempo da operação excedido; o subprocesso foi encerrado."
                     if isinstance(exc, subprocess.TimeoutExpired)
                     else "Falha no subprocesso local; nenhuma credencial é incluída neste erro.")
            return {"jsonrpc": "2.0", "id": message["id"], "result": {
                "content": [{"type": "text", "text": error}], "isError": True}}
    # Discovery, ping and notifications never read a vault or start workers.
    return bridge.dispatch(message)


def main():
    for key in list(os.environ):
        if key.startswith(("CONTROL_PLANE_", "OPENAI_")):
            os.environ.pop(key, None)
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    for raw in iter(lambda: sys.stdin.buffer.readline(bridge.MAX_BYTES * 8 + 1), b""):
        if len(raw) > bridge.MAX_BYTES * 8:
            break
        try:
            response = dispatch(json.loads(raw))
        except (ValueError, UnicodeError):
            response = {"jsonrpc": "2.0", "id": None,
                        "error": {"code": -32700, "message": "Parse error"}}
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
