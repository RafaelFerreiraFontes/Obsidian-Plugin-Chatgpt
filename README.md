# Obsidian Vault Bridge — 0.1.1

Protótipo de plugin local para ChatGPT Desktop/Codex com um servidor MCP stdio em Python. Não afiliado ao Obsidian. Não requer chave da API OpenAI e não abre porta de rede.

## O que foi implementado

| Operação | Implementação e limite |
|---|---|
| Selecionar/autorizar vault | Seletor nativo de pasta; exige `.obsidian`. Consentimentos separados para leitura, escrita e CLI. |
| Ler e buscar | `.md` e `.base`, busca literal, paginação, até 1 MiB por arquivo. |
| Citar | Caminho relativo, linhas, SHA-256 e URI `obsidian://open?path=...`; referência local, não citação web nativa do ChatGPT. |
| Criar/editar | Hash esperado obrigatório; `new` para criação. Backup anterior à substituição. Pasta de destino deve existir. |
| Fórmulas | Texto LaTeX em Markdown; gerador de `.base` com fórmula e tabela. Obsidian valida e avalia a expressão. |
| Consultar instância | CLI oficial: plugins instalados, IDs de comandos, Bases, consulta de Base. |
| Gerenciar plugins | CLI oficial: instalar, habilitar, desabilitar, desinstalar. Confirmação nativa em cada ação. |
| Executar comandos | IDs da paleta do Obsidian; confirmação nativa em cada ação. Não oferece shell nem `eval`. |
| Revogar | Remove a autorização da ponte; não desinstala plugins já instalados. |

## Chat e Codex

O pacote padrão usa stdio local. Chat sem executor local precisa de Secure MCP Tunnel; o indicador conectado não comprova acesso ao diretório. Veja [configuração e diagnóstico do Chat](docs/CHAT.md). A versão 0.1.1 prepara esse caminho, mas não cria credenciais nem provisiona um túnel automaticamente.

## Requisitos e instalação

1. Python 3.10+ com Tkinter disponível pelo comando `python` no PATH do aplicativo. No Windows, o instalador oficial do Python inclui Tkinter. Se `python` abrir a Microsoft Store, ajuste o PATH/aliases do Windows antes de usar.
2. Para operações na instância: instalador Obsidian 1.12.7+; em **Settings → General → Command line interface**, habilite e registre a CLI no PATH. Reinicie o aplicativo host para atualizar o PATH. Abra o vault no Obsidian.
3. Instale o plugin privado pelo link retornado pelo Plugin Creator em um host que ofereça execução local de MCP stdio. A criação na conta não instala Python nem prova compatibilidade da sua versão do aplicativo.
4. Em um chat local com o plugin selecionado, peça: **“Verifique o estado da ponte e autorize um vault do Obsidian.”** A ferramenta `authorize_vault` abre uma janela nativa. Escolha a pasta e conceda apenas as permissões desejadas. Nenhum vault vem autorizado no pacote.
5. Teste primeiro leitura de uma nota sem dados sensíveis. Depois crie uma nota de teste. A autorização de escrita permite edições subsequentes pelo plugin; não abre uma confirmação para cada edição de nota.

Se a ferramenta não aparecer, a conexão/instalação ainda não foi concluída. Não use `python server/bridge.py` como aplicativo interativo: ele espera mensagens MCP. Para um cliente MCP local configurável, use o `mcp.json` incluído; `${PLUGIN_ROOT}` é expandido pelo host de plugins, não pelo terminal.

## Exemplos de uso

- “Busque `projeto Aurora` no vault e cite as linhas relevantes.”
- “Leia `Projetos/Aurora.md` e atualize o status, preservando o restante.”
- “Crie `Custos.base`, fórmula `total` igual a `price * quantity`.”
- “Liste os plugins instalados no vault.”
- “Instale o plugin com ID que eu fornecer.” Instalar e habilitar são ações separadas.
- “Liste os comandos disponíveis e execute o ID que eu escolher.”
- “Revogue o acesso a este vault.”

## Dados e segurança

Autorizações, auditoria e backups ficam em `%LOCALAPPDATA%\ObsidianVaultBridge` no Windows. No Linux/macOS, o fallback é `~/.local/share/ObsidianVaultBridge`. Não são incluídos no ZIP. O histórico registra caminhos e ações, sem texto das notas. Backups contêm o texto anterior completo; não são criptografados e não têm expiração automática. Remova-os manualmente quando apropriado. Revogar não apaga backups nem conteúdo já enviado ao contexto do modelo.

A ponte só aceita caminhos relativos de `.md`/`.base`, bloqueia configurações/pastas ocultas, traversal, ADS, nomes de dispositivo, symlinks, junctions e arquivos com hard links. Não há exclusão de notas, alteração direta de `.obsidian`, execução de shell, JavaScript arbitrário, uploads autônomos ou servidor HTTP. Consultas à CLI verificam se o caminho do vault corresponde ao autorizado; se não corresponder, falham.

Conteúdo lido pela ferramenta entra no contexto do ChatGPT e fica sujeito às configurações de dados da conta. “Local” descreve onde a ponte executa e onde os arquivos permanecem, não significa inferência do modelo offline. A instalação de plugins pelo próprio Obsidian pode acessar a internet. Comandos e plugins autorizados podem ter efeitos fora do vault: o seletor não os transforma em uma sandbox.

Este é um protótipo para um usuário local cooperativo. A configuração é um arquivo do próprio usuário, não uma barreira contra outros processos da mesma conta. A checagem de hash e a troca de arquivo reduzem conflitos, mas não garantem transação com o editor Obsidian/Sync: existe uma janela entre a última leitura e a substituição. Também não há proteção completa contra um processo malicioso que troque caminhos simultaneamente. Para uma versão de produção, use um companion Obsidian com `Vault.process()` e IPC autenticado, ou primitivas específicas do sistema operacional. Pastas/junctions sincronizadas pelo OneDrive podem ser rejeitadas; teste em um vault local simples antes.

## Validação e estado da entrega

Execute `python -m unittest discover -s tests -v` na pasta do plugin. Os testes usam um vault temporário e incluem processo MCP real, validação de ferramentas, conflitos, backups, limites, bloqueios de caminhos e simulação da CLI/confirmações. Não instalam plugins, não abrem autorização e não usam suas notas.

O relatório `VALIDACAO.md` acompanha esta entrega. Testes simulados não confirmam integração com uma instância real. A seleção nativa e o Obsidian CLI precisam de validação pelo usuário no computador onde o plugin for instalado.

## Arquivos

- `plugin.json`: manifesto portátil Agent Plugins 1.0, marcado para execução local.
- `mcp.json`: inicialização do servidor stdio.
- `server/bridge.py`: implementação, sem dependências pip.
- `skills/obsidian-vault/SKILL.md`: fluxo de uso e tratamento de notas como dados não confiáveis.
- `tests/test_bridge.py`: verificação automatizada.
- `docs/ARQUITETURA.md`: decisões, fontes e evolução.
