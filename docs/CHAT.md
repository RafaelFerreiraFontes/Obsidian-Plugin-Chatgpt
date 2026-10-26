# Acesso no Chat: transporte e ativação

## Diagnóstico de 26/10/2026

O código original, o pacote da conta e a instalação Codex usam o mesmo MCP
stdio: `python ${PLUGIN_ROOT}/server/bridge.py`. Não existe endpoint HTTP,
OAuth, chave de API ou relay no pacote 0.1.0. O manifesto declara
`requires_local_executor=true`; a conversão da conta gerou `.mcp.json` e
`.codex-plugin/plugin.json` equivalentes. Não foi encontrada divergência de
transporte entre esses manifestos.

A instalação Codex respondeu a `bridge_status` e a `list_notes(limit=1)` no
vault já autorizado. Isso comprova leitura de diretório pelo processo local.
Não prova execução no Chat. As concessões são locais, em
`%LOCALAPPDATA%/ObsidianVaultBridge/grants.json`, por usuário do Windows; trocar
de computador ou usuário não transfere autorização. Não copie esse arquivo
para a nuvem nem inclua o vault no pacote.

As respostas do Chat anterior não puderam ser recuperadas integralmente pela
ferramenta de histórico: aparecem como referências de conteúdo. Portanto, não
há um erro de execução do Chat capturado que permita atribuir a falha a uma
exceção específica. A explicação sustentada pelo pacote e pela documentação
é a ausência de rota local em um Chat sem executor local. O indicador
“conectado” não demonstra que o processo Python iniciou naquele modo.

A inspeção de permissões pelo ID do plugin retornou `not_installed`, embora
as ferramentas locais estejam disponíveis neste Codex; a pesquisa por nome
não retornou correspondências. Esse resultado não prova desinstalação local
nem bloqueio por permissão. Nenhuma permissão foi ampliada.

## Comparação

| Aspecto | Codex local | Chat sem executor local |
|---|---|---|
| Processo | Python iniciado pelo host | Precisa alcançar o processo por transporte remoto |
| Endpoint atual | Pipes stdio, sem URL | Não há rota no pacote original |
| Autenticação atual | Conta local e concessão nativa do vault | “Conectado” não autentica acesso ao disco |
| Solução preparada | Manter `mcp.json` local | Secure MCP Tunnel até o mesmo Python no PC |
| Permissões de arquivos | Seletor e grants locais | Os mesmos grants; o túnel não concede novos vaults |
| Verificação real | Estado e listagem realizados | Pendente de provisionamento e chamada no Chat |

Não basta mudar stdio para HTTP, retirar `requires_local_executor`, adicionar
`localhost` ou trocar o nome da CLI. Um servidor na nuvem não vê o disco do PC.
Um Chat com executor local compatível pode usar o pacote stdio; confirme as
ferramentas e faça uma chamada real nesse modo.

## Ativar o caminho do Chat

1. Na [OpenAI Platform — túneis](https://platform.openai.com/settings/organization/tunnels),
   crie um Secure MCP Tunnel na organização correta e associe à conta/workspace
   ChatGPT que usará a ponte. São necessários Tunnels Read + Manage para criar;
   Tunnels Read + Use para executar. Reutilize um túnel existente se houver.
2. Instale `tunnel-client` pelo link da Platform ou pelo
   [repositório oficial](https://github.com/openai/tunnel-client/releases/latest).
   Confira `tunnel-client help quickstart` da versão instalada. O helper usa os
   comandos publicados atualmente; não baixa nem executa binários automaticamente.
3. Configure `CONTROL_PLANE_API_KEY` somente no ambiente local do processo, com
   uma chave restrita de runtime. Não coloque o valor em comandos, arquivos do
   projeto, capturas ou mensagens. O helper nunca imprime esse valor.
4. Na pasta do projeto, execute os comandos abaixo, substituindo o ID indicado
   pelo ID real obtido da Platform. O helper recusa IDs ausentes ou malformados.

   ```powershell
   python tools/chat_tunnel.py check
   python tools/chat_tunnel.py init --tunnel-id <ID_REAL>
   python tools/chat_tunnel.py doctor
   python tools/chat_tunnel.py run
   ```

   `init` configura um perfil do cliente oficial fora do pacote; não concede
   acesso a vaults. `run` deve permanecer ativo no mesmo usuário Windows e no
   computador que contém o vault. As janelas de autorização/ações da CLI
   continuam sendo locais e exigem interação humana.
5. Mantenha o plugin privado e de uso pessoal. Esta ponte não implementa
   isolamento entre usuários de um workspace: todos alcançariam os grants do
   processo local. Não compartilhe o túnel/plugin com outros usuários. O caminho
   de túnel usa as permissões da Platform/workspace; não há porta pública aberta.
6. Para atualizar o MESMO plugin da conta, gere um candidato separado:

   ```powershell
   python tools/chat_tunnel.py package --tunnel-id <ID_REAL> --output <ZIP_FORA_DO_PROJETO>
   ```

   O ZIP preserva nome e apresentação e substitui o transporte por
   `streamable-http` com `extensions.com.openai.tunnelId`. Não inclui URL,
   credenciais, dados do vault, servidor stdio ou configurações legadas
   adivinhadas. O `auth.type=none` descreve a ausência de OAuth adicional da
   ponte; o túnel continua sujeito à autenticação e às permissões da OpenAI.
   Valide ID, associação e readiness antes de atualizar a conta. Após ingestão,
   confira as configurações de compatibilidade regeneradas pelo Plugin Creator
   para garantir ausência de stdio obsoleto e de marcação local no perfil remoto.
   Nunca publique um ID fictício dos testes.

   O gerador não atualiza a conta nem substitui o pacote stdio local. Um perfil
   remoto publicado também dependerá do túnel quando usado pelo Codex. A cópia
   local permanece disponível para execução direta. Não se devem juntar stdio
   e remoto no mesmo perfil e presumir compatibilidade no Chat.
7. No Chat de destino, selecione o plugin atualizado e execute `bridge_status`,
   `list_notes(limit=1)` e uma leitura curta de nota escolhida pelo usuário.
   Compare vault_id, permissões, linhas/hash e URI. Só então marque Chat como
   validado. Repita uma chamada no Codex com o perfil que ele efetivamente usa.

## Estado da implementação

0.1.1 adiciona diagnóstico de acessibilidade do diretório, instruções MCP de
inicialização e um helper de configuração/empacotamento do túnel. Um grant
salvo continua separado da verificação de diretório e da leitura de nota.
`note_read_verified=false` significa que o status NÃO leu notas.

O usuário informou que não possui túnel. O cliente oficial também não está
instalado neste ambiente. Não foram criadas chaves ou infraestrutura, enviado
pacote remoto, nem demonstrado acesso no Chat. A correção de transporte está
preparada, mas a falha relatada permanece pendente de ativação e teste ponta a
ponta. Testes unitários de um ZIP não validam ingestão nem autenticação real.

## Fontes oficiais consultadas

- [MCP no ChatGPT e Codex](https://learn.chatgpt.com/docs/extend/mcp)
- [Plugins com execução local](https://developers.openai.com/plugins/deploy/desktop-only)
- [Secure MCP Tunnel: requisitos, comandos, autenticação e ChatGPT](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)

As instruções de pacote usadas pelo gerador seguem também a documentação
`zip-requirements.md` da skill Plugin Creator instalada: `tunnelId` exige
servidor remoto e não pode coexistir com `url`/`server_url`. A aceitação desse
candidato na conta de destino ainda não foi testada.
