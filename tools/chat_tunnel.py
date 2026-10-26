"""Prepare the official tunnel client or a tunnel-backed plugin package.

No credentials are read from files, printed, or included in the package.
Provisioning and a successful Chat call are still required.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PROFILE = "obsidian-vault-bridge"


def tunnel_id(value):
    if not re.fullmatch(r"tunnel_[a-z0-9]{32}", value):
        raise argparse.ArgumentTypeError("Informe o ID real do túnel: tunnel_ + 32 caracteres.")
    return value


def client_command(action, identifier=None, executable="tunnel-client", python=None):
    if action == "init":
        tunnel_id(identifier or "")
        # Forward slashes avoid Windows backslashes being interpreted by the
        # client's command-string parser. Quote both executable and script.
        command = " ".join(json.dumps(str(p).replace("\\", "/")) for p in
                           [python or sys.executable, ROOT / "server/bridge.py"])
        return [executable, "init", "--sample", "sample_mcp_stdio_local",
                "--profile", PROFILE, "--tunnel-id", identifier, "--mcp-command", command]
    if action not in {"doctor", "run"}:
        raise ValueError("Ação desconhecida")
    result = [executable, action, "--profile", PROFILE]
    if action == "doctor":
        result.append("--explain")
    return result


def package(identifier, output, registered_app_id=None):
    """Build a separate candidate; never mutate the local installation."""
    tunnel_id(identifier)
    if not registered_app_id or not re.fullmatch(r"asdk_app_[A-Za-z0-9_-]+", registered_app_id):
        raise ValueError("Registre e conecte o MCP no ChatGPT primeiro; informe seu --app-id real.")
    output = Path(output).resolve()
    if output.is_relative_to(ROOT):
        raise ValueError("Salve o ZIP fora da pasta do plugin.")
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8-sig"))
    remote = copy.deepcopy(manifest)
    remote["extensions"]["com.openai"]["requires_local_executor"] = False
    remote["extensions"]["com.openai"]["apps"] = "./.app.json"
    mcp = {"$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
           "mcpServers": {"obsidian-vault-bridge": {
               "type": "streamable-http", "extensions": {"com.openai": {
                   "tunnelId": identifier, "auth": {"type": "none"}}}}}}
    # Tunnel/workspace authorization protects this route; this is not a public
    # unauthenticated HTTP listener. No URL or localhost endpoint is invented.
    files = {"plugin.json": json.dumps(remote, ensure_ascii=False, indent=2),
             "mcp.json": json.dumps(mcp, indent=2),
             ".app.json": json.dumps({"apps": {"obsidian-vault-bridge": {
                 "id": registered_app_id}}}, indent=2)}
    # The account ingester owns generated compatibility files. Read them back
    # after any future upload rather than guessing its legacy tunnel encoding.
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
        # Explicit allowlist: never ship grants, backups, environment or keys.
        for name in ["assets/icon.svg", "skills/obsidian-vault/SKILL.md"]:
            archive.write(ROOT / name, name)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["check", "init", "doctor", "run", "package"])
    parser.add_argument("--tunnel-id", type=tunnel_id)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--app-id", help="ID real asdk_app_ da conexão registrada no ChatGPT")
    args = parser.parse_args()
    if args.action in {"init", "package"} and not args.tunnel_id:
        parser.error("--tunnel-id é obrigatório; provisione o túnel na OpenAI Platform.")
    if args.action == "package":
        if not args.output:
            parser.error("--output é obrigatório")
        if not args.app_id:
            parser.error("--app-id é obrigatório; mcp.json sozinho não registra ferramentas no Chat.")
        print(package(args.tunnel_id, args.output, args.app_id))
        print("Candidato gerado; ID, associação à conta e acesso no Chat ainda precisam de validação.")
        return 0
    executable = shutil.which("tunnel-client")
    key_present = bool(os.environ.get("CONTROL_PLANE_API_KEY"))
    if args.action == "check":
        print(json.dumps({"client_installed": bool(executable),
                          "runtime_key_present": key_present,
                          "chat_access_verified": False}))
        return 0 if executable and key_present else 2
    if not executable:
        parser.error("tunnel-client não instalado. Consulte docs/CHAT.md.")
    if not key_present:
        parser.error("Defina CONTROL_PLANE_API_KEY localmente; não a envie no chat.")
    return subprocess.run(client_command(args.action, args.tunnel_id, executable),
                          shell=False, cwd=ROOT).returncode


if __name__ == "__main__":
    raise SystemExit(main())
