Atualização 0.1.4: execução automática em segundo plano, com worker temporário por operação e chave DPAPI. Consulte docs/EXECUCAO-AUTOMATICA.md (ou EXECUCAO-AUTOMATICA.md nesta pasta). Instruções anteriores que exigem manter o terminal aberto são históricas e foram substituídas.

# Implantação e verificação no Chat — 26/10/2026

## Resultado real

O teste no chat existente **Conectar Vault Obsidian** executou bridge_status
e list_notes(limit=1) com o plugin ORIGINAL selecionado pelo @. O status
confirmou o vault já autorizado e diretório acessível. A listagem retornou
uma nota e next_offset=1. Nenhum conteúdo de nota foi lido, nenhuma nota foi
escrita e nenhuma ação de CLI/autorização foi executada.

O cliente oficial registrou encaminhamento de chamadas ao processo stdio.
Depois do teste, /healthz e /readyz responderam HTTP 200, live e ready.
O baseline Codex anterior também retornou estado e listagem reais. A sessão
Codex existente manteve seu processo 0.1.0 até a mudança de configuração;
não foi tratada como prova do novo caminho remoto. Não foi validada a recarga
automática do pacote no Codex nem executada escrita real em nenhum modo.

## Causa e correção

Havia duas condições distintas:

1. O pacote original apenas iniciava Python por stdio no computador do usuário.
   O Chat sem executor local não tinha rota até esse processo.
2. Mesmo com Secure MCP Tunnel ativo e mcp.json remoto salvo, as ferramentas
   ainda não apareciam no Chat: faltava registrar a conexão MCP no ChatGPT e
   mapear o aplicativo registrado no plugin original.

O usuário criou o túnel e a chave, inseriu a chave em entrada local protegida,
registrou/conectou o servidor MCP na interface do ChatGPT. Depois foi adicionado
ao plugin original o vínculo extensions.com.openai.apps -> ./.app.json com o
ID real do aplicativo registrado. A identidade do plugin original foi mantida.

As tentativas antes desse vínculo falharam tanto com referência textual quanto
com seleção explícita pelo @. O teste depois do vínculo funcionou. Isso separa
pacote salvo, cliente de túnel saudável, conexão MCP registrada e acesso real.

## Identificadores (não são credenciais)

- Plugin original: plugins_6adf13273cf081918e9a71128212ce9d
- Aplicativo MCP: asdk_app_6adf253a5f9c819191c6a370f65bea01
- Conexão técnica gerada pelo ChatGPT: plugin_asdk_app_6adf253a5f9c819191c6a370f65bea01
- Túnel: tunnel_6adf20f8028c8191ac3a2d02fb08392f

A conexão técnica aparece como **Obsidian Vault Bridge — conexão MCP** e é a
dependência que fornece as ferramentas. O plugin original continua oferecendo
a habilidade e o vínculo com essas ferramentas. Não excluir essa conexão.
Nenhum plugin foi tornado público ou compartilhado.

## Configuração fonte

- Raiz do projeto: perfil local stdio preservado para Codex.
- profiles/chat/: manifesto e conexão da distribuição da conta, com aplicativo
  registrado e transporte remoto. O manifesto de perfil é um componente; o
  pacote também precisa das habilidades e assets da raiz.
- tools/chat_tunnel.py: package agora exige --app-id real, além de --tunnel-id.
  Um pacote contendo somente mcp.json não registra as ferramentas no Chat.
- As configurações mcp.json/.mcp.json da conta foram preservadas. A revisão
  automática rejeitou sua remoção; foi aplicada a alternativa aditiva com
  .app.json. Não houve exclusão de configurações.

## Operação e credenciais

Cliente oficial Windows AMD64 v0.0.18, ZIP conferido por SHA-256:
8d0da1ce79532d44ccc5ed5d8bd36cdfffba37dfd287c602d69635c8bb5db2b2.
Perfil com referência env:CONTROL_PLANE_API_KEY; nenhuma chave foi gravada no
repositório, pacote ou mensagens. A entrada protegida usa a chave somente no
ambiente do processo. Os logs nativos não foram configurados para HTTP bruto.

O processo foi iniciado numa janela interativa de PowerShell que deve continuar
aberta. Não é um serviço com inicialização automática. Ao encerrar a janela,
desligar o PC, expirar/revogar a chave ou parar o cliente, Chat perde essa rota.
Para iniciar de novo, use o inicializador entregue em outputs nesta conversa
e informe localmente a chave restrita. Não cole a chave no chat.

A chave foi preparada com somente Tunnels Read + Use e validade de 30 dias.
O usuário realizou a criação. A janela não grava a chave para próximos inícios.
O processo responde com versão de servidor **0.1.1**. A versão do pacote pode
ser superior porque mudanças posteriores foram de conexão/empacotamento;
essas versões têm ciclos distintos e não indicam, sozinhas, erro de recarga.

## Limites de validação

- Listagem real no Chat comprovada; leitura do texto de notas, escrita e CLI
  reais não foram exercitadas, conforme o escopo autorizado do teste.
- 28 testes automatizados: 27 passaram, 1 ignorado (symlink indisponível).
- Sem isolamento entre vários usuários do workspace: manter uso pessoal privado.
- O servidor só deve continuar acessando os grants nativos já concedidos.

Fontes: [registro e teste de MCP no ChatGPT](https://developers.openai.com/plugins/deploy/connect-chatgpt),
[mapeamento de aplicativos em plugins](https://developers.openai.com/plugins/build/plugins),
[Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels).

Release final da conta: 0.1.3, pluginrel_6adf27096ea88191a7f90cfcc939b380. Read-back confirmou identidade, apresentação, escopo USER/PRIVATE, vínculo do app e preservação dos dois arquivos MCP. A validação real de Chat ocorreu em 0.1.2; 0.1.3 preserva a mesma conexão e atualiza o gerador e a documentação. Nenhuma mudança foi feita ao servidor em execução.
