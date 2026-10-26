Atualização 0.1.4: execução automática em segundo plano, com worker temporário por operação e chave DPAPI. Consulte docs/EXECUCAO-AUTOMATICA.md (ou EXECUCAO-AUTOMATICA.md nesta pasta). Instruções anteriores que exigem manter o terminal aberto são históricas e foram substituídas.

Estado atualizado: a conexão registrada foi vinculada ao plugin e o teste real de listagem no Chat funcionou. Consulte docs/IMPLANTACAO-CHAT.md (ou IMPLANTACAO-CHAT.md nesta pasta) para evidências, versões e operação. As pendências descritas abaixo registram a investigação anterior.

# Validação — 0.1.1 — 26/10/2026

## Resultado desta alteração

- 27 testes executados: 26 passaram; 1 ignorado (symlink indisponível no Windows).
- Execução final fora do ambiente restrito, com vaults temporários, sem notas reais.
- Hard links e junctions reais testados; concessões, conflitos e backups continuam verificados.
- MCP stdio real testado, incluindo descoberta e chamada de status.
- Novos testes: diretório indisponível/negado sem confundir grant com acesso;
  instruções de inicialização; ID de túnel inválido/ausente; argumentos com espaços;
  perfil compartilhado entre doctor/run; pacote remoto sem credenciais/dados locais;
  preservação de identidade, prompt e configuração local; recusa de sobrescrita.
- Tentativas anteriores no ambiente restrito falharam por permissões de temporários/links.
  Esses resultados não foram tratados como defeitos do plugin; a execução final acima passou.

## Integração real

Codex: ferramentas INSTALADAS 0.1.0 responderam bridge_status e list_notes(limit=1)
no vault autorizado. Leitura de diretório confirmada; nenhuma nota foi escrita ou
plugin Obsidian instalado. Isso é baseline da instalação atual, não prova da
recarga automática do código 0.1.1 nem do transporte remoto.

Código 0.1.1: testes de processo MCP real em arquivos temporários passaram.
A instalação da conta permanece 0.1.0; não houve publicação ou edição do cache.

Chat: NÃO validado. O usuário informou ausência de túnel. Preflight do helper:
client_installed=false, runtime_key_present=false, chat_access_verified=false.
Não há tunnel_id real, chave restrita, associação à conta/workspace ou cliente
ativo. O gerador de pacote foi testado com fixture sintética, nunca enviada à
conta. Ingestão do pacote remoto, chamadas pelo túnel e autenticação reais
permanecem pendentes. Ver docs/CHAT.md.

A investigação não recuperou as respostas completas da conversa Chat, apenas
referências de conteúdo. A ausência de rota stdio para um Chat sem executor
local é sustentada pela arquitetura; a falha específica no cliente Chat não
foi reproduzida com uma captura de erro. Não afirmar resolução ponta a ponta.

O relatório original 0.1.0 está preservado no commit inicial
982bcef5023a6e7060af1ce820aa5532bacc0a49.

Validação 0.1.4: 35 testes, 34 aprovados e 1 ignorado (symlink). No Chat, status duas vezes retornou PIDs distintos, ambos confirmados encerrados pelo Windows; list_notes(limit=1) passou. Runtime gerenciado permaneceu running/healthy/ready sem janela. Parada/reinício via chave DPAPI e reexecução da entrada Startup foram testados. Logout/login completo e escrita/CLI em dados reais não foram testados.
