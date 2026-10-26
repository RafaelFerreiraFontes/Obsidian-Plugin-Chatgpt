# Execução automática no Windows — 0.1.4

## Comportamento

O cliente do Secure MCP Tunnel e um pequeno gateway de controle permanecem em
segundo plano, sem terminal. Cada chamada MCP tools/call inicia um processo
Python separado para a operação. O worker encerra e é coletado antes de o
resultado voltar ao Chat. Descoberta, initialize e ping não iniciam workers
e não acessam o vault.

Não há uma nova janela a cada uso. As janelas nativas de seleção de vault e
confirmação de comandos/plugins continuam aparecendo quando essas operações
específicas são solicitadas. As permissões nativas não foram contornadas.

Operação significa uma chamada de ferramenta, não a conversa inteira. Uma
resposta que faz três chamadas usa três workers sequenciais. O gateway e o
túnel ficam disponíveis para receber a próxima chamada; encerrar também esse
canal impediria o Chat de enviar o pedido de reativação.

## Inicialização e credencial

O instalador tools/windows_background.ps1 usa o mecanismo oficial
tunnel-client runtimes connect e cria uma entrada somente no Startup do
usuário atual. Ao entrar no Windows, um PowerShell oculto inicia/reutiliza o
runtime e encerra; o daemon gerenciado e o gateway seguem em segundo plano.
Não é um serviço do sistema e não requer senha de conta do Windows.

O cliente oficial é instalado em %LOCALAPPDATA%/ObsidianVaultBridgeRuntime/bin.
O ZIP original é conferido por SHA-256 antes da extração. A configuração e a
chave ficam no diretório local do runtime, fora do repositório e dos pacotes.
A chave é armazenada com DPAPI do usuário via SecureString, com ACL de diretório
restrita ao usuário atual e SYSTEM. Ela só é descriptografada no processo de
inicialização e fornecida ao cliente pela variável CONTROL_PLANE_API_KEY.
Não é colocada em argumentos, mensagens ou código-fonte.

O gateway remove variáveis CONTROL_PLANE_* e OPENAI_* de seu ambiente; os
workers também recebem um ambiente sem essas credenciais. DPAPI/ACL não
protegem contra administrador ou processos maliciosos do mesmo usuário.

O instalador pode solicitar a chave novamente ao atualizá-la. Expiração,
revogação, PC desligado ou encerramento de sessão interrompem a disponibilidade.
Não há promessa de iniciar o PC remotamente ou funcionar sem sessão Windows.

## Comandos de controle

Na pasta do projeto:

```powershell
# Consultar o runtime gerenciado
./tools/windows_background.ps1 -Action Status
# Iniciar de forma idempotente usando a chave já protegida
./tools/windows_background.ps1 -Action Start
# Parar até a próxima entrada no Windows/inicialização manual
./tools/windows_background.ps1 -Action Stop
# Parar e remover a inicialização automática (mantém a chave criptografada)
./tools/windows_background.ps1 -Action Disable
```

A raiz mcp.json local usa server/operation_gateway.py. O cliente de túnel
gerenciado usa o mesmo gateway. O perfil Chat da conta continua vinculado ao
aplicativo registrado; não foi criado outro túnel nem outra chave.

## Limites e testes

Cada worker tem um limite de 110 segundos para reservar margem no prazo de
120 segundos do túnel. Em timeout, subprocess.run encerra/coleta o worker.
Se uma operação mutante expirar, confira seu efeito antes de repeti-la.
O encerramento de um worker não reverte uma escrita já concluída nem para
a instância principal do Obsidian ou um plugin externo já instalado.

Os grants são relidos a cada operação; a revogação é respeitada no próximo
worker. Não foram ampliadas permissões do vault.

Testes cobrem dois workers reais com PIDs diferentes, término antes da
resposta, revogação entre chamadas, timeout real, resposta inválida e remoção
de credenciais do ambiente. O runtime instalado foi iniciado, parado e
reiniciado com a chave criptografada; repetição de Start reutilizou o processo.
Saúde/prontidão e ausência de janela foram verificadas. A entrada de Startup
foi inspecionada e executada; não foi feito logout/login completo do Windows.

Fonte: [Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels).

Validação real no Chat: bridge_status retornou versão 0.1.4 e worker_pid 21672 e 31916 em duas chamadas. list_notes(limit=1) funcionou. Verificação posterior pelo Windows encontrou zero desses workers ativos e zero workers de operação do projeto; o runtime gerenciado continuava running/healthy/ready, sem janela (MainWindowHandle=0). Nenhuma nota foi alterada.
