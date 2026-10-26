# Validação — 26/10/2026

Versão: 0.1.0. Python 3.10, Windows. Resultado: **17 testes executados, 16 passaram e 1 foi ignorado**.

Verificado em arquivos temporários:

- Processo MCP stdio real: inicialização, descoberta de 11 ferramentas e chamada de estado sem autorização prévia.
- Leitura UTF-8, linhas, hash, URI e tratamento de arquivos vazios.
- Criação exclusiva, substituição com versão esperada, backup e rejeição de edição desatualizada.
- Rejeição de caminhos externos, caminhos absolutos, configurações ocultas, ADS e nomes especiais do Windows.
- Rejeição de hard links e junctions reais; junctions também não entram na listagem.
- Permissão somente leitura, revogação, busca literal, paginação e limite de tamanho.
- Geração de Base com fórmula preservada como texto.
- Validação de argumentos MCP.
- CLI simulada: recusa de vault diferente, argumentos fixos sem shell e confirmação nativa obrigatória antes de instalar plugin.

O teste com symlink foi ignorado porque o Windows não permitiu criar symlinks nesta sessão. A verificação implementada usa `lstat` e o atributo reparse point; isso não substitui o teste pendente com symlink real.

Não verificado: instalação/descoberta no aplicativo ChatGPT alvo, interação humana com o seletor de pasta, execução em um vault real, avaliação de fórmula no Obsidian e comandos/instalação de plugins pela CLI real. A CLI não foi encontrada no PATH disponível durante a investigação. Nenhum vault do usuário foi autorizado ou modificado.

Limites conhecidos: janela de concorrência com editores/Sync e outros processos; não é sandbox contra o mesmo usuário. O README explica esses limites e a evolução para um companion com `Vault.process()`.

O empacotamento verifica os manifestos JSON, campos essenciais, referência do ícone, cabeçalho da skill e integridade/inventário do ZIP. Isso não equivale a certificação integral dos schemas externos nem aprovação para distribuição pública.
