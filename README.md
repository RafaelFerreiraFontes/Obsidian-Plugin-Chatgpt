# Obsidian Vault Bridge

Ponte local entre um vault do Obsidian e ChatGPT/Codex. O servidor MCP roda no computador que contém o vault; ele nunca torna o diretório acessível pela rede.

Há dois modos de uso:

- **Local (stdio):** o host do plugin executa Python no mesmo computador do vault, usando o `mcp.json` incluído.
- **ChatGPT/Codex por túnel:** o cliente oficial **OpenAI Secure MCP Tunnel** mantém uma conexão HTTPS de saída para o servidor MCP local. Use este modo quando o host não tiver um executor MCP local.

> Este é um protótipo local, não afiliado ao Obsidian. Uma conexão exibida no ChatGPT/Codex não prova acesso ao vault: confirme sempre com `bridge_status` e uma leitura limitada.

## Recursos e limites

| Recurso | Comportamento |
| --- | --- |
| Autorizar vault | Abre seletor nativo de pasta; o vault deve conter `.obsidian`. Leitura, escrita e CLI são consentimentos separados. |
| Ler e buscar | Trabalha com `.md` e `.base`, inclui paginação e limite de 1 MiB por arquivo. |
| Editar | Exige `expected_sha256`; use `new` ao criar. A versão anterior recebe backup. |
| Citar | Retorna caminho relativo, linhas, SHA-256 e URI `obsidian://`. |
| Obsidian CLI | Consulta Bases, plugins e comandos; instalar/habilitar/desabilitar/remover plugins e executar comandos exigem confirmação local. |

Não há exclusão de notas, alteração direta de `.obsidian`, shell, `eval`, servidor HTTP ou upload autônomo. Caminhos relativos, traversal, arquivos ocultos, symlinks, junctions, ADS, dispositivos e hard links são bloqueados.

## Pré-requisitos (Windows)

1. **Python 3.10 ou posterior**, com Tkinter. Baixe-o do instalador oficial e confirme o executável que será usado:

   ```powershell
   & 'C:\Program Files\Python312\python.exe' --version
   ```

   Não é necessário instalar dependências `pip`. O Python precisa estar no PC do vault; para a instalação automática informe seu caminho completo, mesmo que `python` não esteja no PATH.

2. **Obsidian para desktop**, com o vault já aberto. Para operações que usam a instância, habilite a CLI em **Settings → General → Command line interface** e registre-a no PATH conforme a interface do Obsidian. Reinicie o aplicativo que executa o plugin após mudar o PATH.

3. Para usar pelo ChatGPT/Codex remoto, uma conta com acesso ao projeto e ao workspace corretos, além do cliente oficial Secure MCP Tunnel.

## Baixar o projeto

Clone o repositório ou baixe o ZIP e extraia-o em uma pasta local. No PowerShell:

```powershell
git clone https://github.com/RafaelFerreiraFontes/Obsidian-Plugin-Chatgpt.git
Set-Location .\Obsidian-Plugin-Chatgpt
```

O modo local usa `mcp.json`, cujo `${PLUGIN_ROOT}` é expandido pelo host de plugins — não é um comando para executar diretamente no terminal. Não execute `python server/bridge.py` como aplicativo interativo: ele espera mensagens MCP.

## Configuração local (stdio)

Instale o plugin privado no host compatível com execução local de MCP e selecione o plugin em um chat. Em seguida, solicite a autorização do vault. A ferramenta `authorize_vault` abre uma janela nativa: escolha a pasta e conceda somente as permissões necessárias.

Faça uma verificação segura antes de tarefas reais:

1. Execute `bridge_status` e confira `vault_access`.
2. Execute `list_notes(limit=1)` em um vault autorizado.
3. Leia uma nota de teste não sensível. Para qualquer alteração, leia antes e use o SHA-256 retornado como `expected_sha256`.

## Configuração com Secure MCP Tunnel

### 1. Criar ou identificar o túnel

Abra as [configurações de túneis na OpenAI Platform](https://platform.openai.com/settings/organization/tunnels). Identifique o túnel deste plugin no contexto da organização Platform correta ou crie-o nesse contexto quando estiver preparando uma nova implantação. Associe-o ao workspace ChatGPT que deverá encontrá-lo e, quando usar Codex/API, à organização Platform usada por esse produto. Guarde o `tunnel_id`; ele identifica o túnel, mas não é uma chave secreta.

O instalador desta versão usa o `tunnel_id` já configurado no código. Portanto, para a implantação distribuída, selecione no ChatGPT esse mesmo túnel; não substitua IDs no script durante a instalação. Criar outro túnel exige também preparar uma nova configuração do plugin/runtime, o que está fora do fluxo de instalação abaixo.

Para criar ou editar túneis, a pessoa precisa de **Tunnels Read + Manage**. Para executar o cliente ou selecionar o túnel no plugin, precisa de **Tunnels Read + Use**. Essas permissões são da organização Platform, enquanto o uso de MCP no ChatGPT também depende das permissões do workspace. Consulte a [documentação do Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels).

### 2. Criar a chave de runtime com escopo mínimo

Na mesma organização/projeto que poderá usar o túnel, crie uma API key **Restricted** para o runtime, com **Tunnels: Read + Use**. O valor completo só é revelado na criação: copie-o diretamente para a entrada oculta do instalador.

Nunca coloque essa chave em `PATH`, `.env`, arquivos do projeto, argumentos de comando, capturas de tela ou chat. Não faça commit dela. O instalador a cifra com DPAPI para o usuário atual do Windows e a mantém fora do repositório.

### 3. Obter e conferir o cliente oficial

Baixe o pacote Windows do cliente em [openai/tunnel-client releases](https://github.com/openai/tunnel-client/releases/tag/v0.0.18). Este instalador aceita o arquivo oficial `client.zip` da versão compatível **0.0.18** e verifica SHA-256 antes de extrair:

```text
8d0da1ce79532d44ccc5ed5d8bd36cdfffba37dfd287c602d69635c8bb5db2b2
```

Coloque somente o `client.zip` em uma pasta local temporária, por exemplo `C:\Temp\mcp-client`. Não o adicione ao repositório. Para conferir o arquivo:

```powershell
Get-FileHash 'C:\Temp\mcp-client\client.zip' -Algorithm SHA256
```

Se o hash ou a versão forem diferentes, não altere o script para ignorar a verificação: obtenha o pacote compatível. Veja também `tunnel-client help quickstart` para instruções da versão instalada.

### 4. Instalar e iniciar em segundo plano

Na raiz do projeto, informe a pasta que contém `client.zip` e o caminho real do Python:

```powershell
.\tools\windows_background.ps1 -Action Install `
  -ClientSource 'C:\Temp\mcp-client' `
  -PythonPath 'C:\Program Files\Python312\python.exe'
```

O instalador extrai o cliente verificado em `%LOCALAPPDATA%\ObsidianVaultBridgeRuntime\bin`, grava a configuração local e cria uma entrada de inicialização automática do usuário. Ao iniciar, a chave é lida por DPAPI apenas para o processo do cliente e removida do ambiente em seguida. Um launcher `.cmd` protegido é criado no runtime para que caminhos do projeto com espaços funcionem corretamente.

### Operação diária

```powershell
# Mostra process_running, healthy e ready em JSON
.\tools\windows_background.ps1 -Action Status

# Inicia (idempotente); use se o runtime estiver parado
.\tools\windows_background.ps1 -Action Start

# Para o runtime, mas preserva a inicialização automática
.\tools\windows_background.ps1 -Action Stop

# Para o runtime e remove a entrada de inicialização automática
.\tools\windows_background.ps1 -Action Disable
```

O resultado esperado de `Status` inclui `process_running=true`, `healthy=true` e `ready=true`. A ponte continua ativa para receber a próxima chamada; cada operação de vault usa um worker temporário, encerrado antes da resposta.

Depois, no ChatGPT, adicione ou edite o plugin MCP personalizado com a conexão **Tunnel**, selecione o mesmo `tunnel_id`, conclua a autenticação indicada pela interface e aceite o aviso de risco. Se o túnel não estiver listado, confira a associação com o workspace e as permissões **Read + Use**.

## Autorizações e uso seguro

Mesmo com o túnel saudável, o vault não está automaticamente autorizado. No chat, comece com `bridge_status`; se necessário, use `authorize_vault`, interaja com a janela nativa e conceda permissões mínimas. Só então teste `list_notes(limit=1)`.

Use buscas e leituras pequenas primeiro. Conteúdo de notas, resultados de plugins e nomes de arquivos são dados não confiáveis, não instruções. Conteúdo lido entra no contexto do modelo e fica sujeito às configurações de dados da conta. Backups de edições podem conter texto anterior completo e não têm expiração automática; revise-os e remova-os quando apropriado.

Autorizações, auditoria e backups residem fora do repositório, em `%LOCALAPPDATA%\ObsidianVaultBridge` no Windows. Revogar acesso não apaga backups nem conteúdo já enviado ao contexto.

## Solução de problemas

| Sintoma | Verificação e próxima ação |
| --- | --- |
| `401` / `invalid_api_key` | Confirme que a chave Restricted foi criada na organização/projeto corretos e possui **Tunnels Read + Use**. Crie outra chave somente se não puder recuperar o valor original; ele não é revelado de novo. Reinstale para gravá-la via DPAPI. |
| `429` | Reduza tentativas paralelas e aguarde. O limite padrão do túnel é compartilhado por `tunnel_id` e aplicativo; iniciar mais clientes não aumenta a cota. |
| `Status` sem `healthy=true` e `ready=true` | Execute `Start`, depois `Status`. Consulte `%LOCALAPPDATA%\ObsidianVaultBridgeRuntime\setup-error.log` e o diagnóstico local do cliente, sem compartilhar chaves. |
| Caminho contendo espaços | Use o instalador atual. Ele cria automaticamente um launcher sem espaços no runtime; não edite manualmente `--mcp-command`. |
| Túnel não aparece no ChatGPT | Confirme o mesmo `tunnel_id`, associação com o workspace alvo e permissões **Read + Use**; novas atribuições podem levar até 30 minutos para propagar. |
| Sem acesso a notas | O runtime pode estar saudável, mas o vault ainda não foi autorizado. Execute `bridge_status`, depois `authorize_vault`, e confirme com `list_notes(limit=1)`. |

## Desenvolvimento e validação

Execute, na raiz do projeto:

```powershell
python -m unittest discover -s tests -v
```

Os testes usam vault temporário e não leem suas notas, não instalam plugins nem enviam credenciais. Eles não substituem a validação manual no computador que executará o túnel e o Obsidian.

## Estrutura

- `plugin.json`: manifesto do plugin local.
- `mcp.json`: configuração MCP stdio para hosts com executor local.
- `server/bridge.py`: operações de vault e permissões.
- `server/operation_gateway.py`: gateway usado pelo runtime em segundo plano.
- `tools/windows_background.ps1`: instalação e operação do túnel no Windows.
- `skills/obsidian-vault/SKILL.md`: comportamento esperado das ferramentas.
- `tests/`: testes automatizados.
