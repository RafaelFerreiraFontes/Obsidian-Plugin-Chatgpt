# Arquitetura e investigação — 26/10/2026

## Caminho escolhido

```text
ChatGPT Desktop / Codex — conversa com execução local
        |
        | MCP stdio, processo gerenciado pelo host
        v
Ponte Python local
        |-- seletor de pasta + consentimento humano nativo
        |-- arquivos Markdown/Bases do vault autorizado
        |-- concessões, auditoria e backups locais
        `-- Obsidian CLI oficial --> instância Obsidian e seus plugins
```

A documentação atual da OpenAI descreve plugins com MCP stdio executados no computador do usuário e a marcação Desktop only. Portanto, não é correto afirmar que todo plugin do ChatGPT só pode usar endpoints públicos, nem presumir que qualquer versão/conta do aplicativo possa iniciar processos locais. A instalação em um chat local compatível precisa ser verificada.

O Plugin Creator aceita um arquivo de pacote e salva um plugin privado. Isso não implanta uma ponte, instala runtime, autoriza pastas ou demonstra que o host carregou o servidor. A distribuição pública de MCP local tem restrição para parceiros aprovados na documentação consultada; criação privada e publicação no diretório são fluxos distintos. Este projeto usa somente o fluxo privado solicitado.

O seletor é do processo local Python/Tkinter. Não é um seletor web fictício nem um recurso de filesystem presumido de uma página MCP App. O servidor começa sem acesso concedido a vault algum. Apenas a interação nativa grava autorizações; as ferramentas não aceitam uma raiz de filesystem fornecida pelo modelo. Usuários podem revogar e executar a autorização novamente para reduzir permissões.

## Por que a CLI oficial

A CLI já oferece `plugins`, `plugin:install`, `plugin:enable`, `plugin:disable`, `plugin:uninstall`, `commands`, `command`, `bases` e `base:query`. Isso evita depender de APIs internas de gerenciamento de plugins do Obsidian. O código usa `subprocess` com lista de argumentos e `shell=False`, sem interpretar uma linha de shell enviada pelo modelo. Cada ação mutante da instância tem confirmação nativa.

A seleção do vault pela CLI depende do diretório de trabalho, conforme a documentação. Antes das chamadas, a ponte executa `vault info=path` no diretório autorizado e compara o caminho retornado. Ela falha se não conseguir confirmar o alvo. Ainda é necessário testar esse comportamento na versão instalada; um contexto de janela/arquivo ativo pode influenciar comandos da paleta. O diálogo informa o risco e não promete confinamento dos comandos.

## Alternativas e evolução

1. **Companion plugin dentro do Obsidian:** preferível quando for necessária edição coordenada com o editor, seleção/arquivo ativo, metadados detalhados e eventos. Usar `app.vault` e `Vault.process()` para alterações com verificação. Definir protocolo de versão, pareamento por token aleatório, transporte por named pipe ou loopback autenticado, limites, revogação e confirmação ligada ao payload exato. Não usar JavaScript arbitrário como API. Não foi implementado nesta versão.
2. **Ponte remota com relay/túnel:** relevante para um host sem processos locais. Exige um agente instalado no PC e transporte MCP remoto suportado; autenticação, isolamento por usuário e pareamento são obrigatórios. Não apontar um servidor cloud para `localhost` esperando acessar o computador do usuário. Não foi criada infraestrutura remota nesta entrega.
3. **Extensões de filesystem do host:** podem oferecer autorização de arquivos em hosts compatíveis; selecionar um arquivo não concede automaticamente acesso geral à máquina ou controle da instância Obsidian. Nenhuma API experimental desse tipo é necessária nesta versão.

## Fórmulas e citações

Uma fórmula pode significar LaTeX, expressão de Bases ou código de um plugin como Dataview. Este pacote implementa autoria de texto LaTeX e geração de Bases; não instala Dataview automaticamente nem avalia código em Python. A Base gerada usa JSON, subconjunto de YAML, com `formulas` e `views`; a expressão é uma string. A validade semântica deve ser verificada no Obsidian.

Citações são verificáveis pela leitura: caminho, linhas, hash e URI local. O arquivo pode mudar depois. Não há integração implementada com a interface de citações nativas do ChatGPT ou garantia de link navegável em todos os clientes.

## Fontes primárias consultadas

- [OpenAI: plugins Desktop only e MCP stdio](https://developers.openai.com/plugins/deploy/desktop-only)
- [OpenAI: empacotamento de plugins](https://developers.openai.com/plugins/build/plugins)
- [ChatGPT Learn: plugins](https://learn.chatgpt.com/docs/plugins)
- [Obsidian: CLI, requisitos e comandos](https://obsidian.md/help/cli)
- [Obsidian: sintaxe de Bases](https://obsidian.md/help/bases/syntax)
- [Obsidian: fórmulas](https://obsidian.md/help/formulas)
- [Obsidian: Vault API e Vault.process](https://docs.obsidian.md/Plugins/Vault)

As afirmações de produto se baseiam nessas fontes; a segurança e a compatibilidade do protótipo dependem da implementação e dos testes locais, não da mera existência da documentação.

## Atualização 0.1.1

O caminho do Chat sem executor local foi detalhado em [CHAT.md](CHAT.md): Secure MCP Tunnel até o mesmo processo stdio. O helper prepara configuração e pacote; não há túnel provisionado nem acesso no Chat demonstrado. O perfil padrão continua stdio local. Consulte VALIDACAO.md para separar testes automatizados, baseline Codex e pendências reais.
