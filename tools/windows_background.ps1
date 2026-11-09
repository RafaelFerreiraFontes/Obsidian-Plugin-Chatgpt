param(
    [ValidateSet('Install','Start','Stop','Status','Disable')][string]$Action = 'Status',
    [string]$ClientSource,
    [string]$PythonPath,
    [string]$RuntimeRoot = (Join-Path $env:LOCALAPPDATA 'ObsidianVaultBridgeRuntime')
)
$ErrorActionPreference = 'Stop'
$aliasName = 'obsidian-vault-bridge'
$configFile = Join-Path $RuntimeRoot 'runtime.json'
$keyFile = Join-Path $RuntimeRoot 'runtime-key.dpapi'
$statusFile = Join-Path $RuntimeRoot 'last-status.json'
$startupFile = Join-Path ([Environment]::GetFolderPath('Startup')) 'Obsidian Vault Bridge.lnk'
$pwshPath = (Get-Process -Id $PID).Path

function Protect-Directory([string]$Directory) {
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    $userSid = [Security.Principal.WindowsIdentity]::GetCurrent().User
    $acl = [Security.AccessControl.DirectorySecurity]::new()
    $acl.SetOwner($userSid)
    $acl.SetAccessRuleProtection($true, $false)
    foreach ($sid in @($userSid, [Security.Principal.SecurityIdentifier]::new('S-1-5-18'))) {
        $rule = [Security.AccessControl.FileSystemAccessRule]::new($sid, 'FullControl', 'ContainerInherit,ObjectInherit', 'None', 'Allow')
        $acl.AddAccessRule($rule)
    }
    Set-Acl -LiteralPath $Directory -AclObject $acl
}

function Read-Config {
    if (-not (Test-Path -LiteralPath $configFile)) { throw 'Execução automática ainda não instalada.' }
    return Get-Content -Raw -LiteralPath $configFile | ConvertFrom-Json
}

function Read-RuntimeStatus($Config) {
    $offline = '{"process_running":false,"healthy":false,"ready":false}'

    try {
        $output = @(
            & $Config.client runtimes status $aliasName --json 2>&1
        )

        $exitCode = $LASTEXITCODE
        $text = ($output | Out-String).Trim()

        if ($exitCode -eq 0 -and $text) {
            return $text
        }

        if ($text -match 'is not known') {
            return $offline
        }

        throw "Falha no status do runtime (codigo $exitCode): $text"
    }
    catch {
        if ($_.Exception.Message -match 'is not known') {
            return $offline
        }

        throw
    }
}

function Is-Ready([string]$Text) {
    return ($Text -match '"process_running"\s*:\s*true' -and
            $Text -match '"healthy"\s*:\s*true' -and $Text -match '"ready"\s*:\s*true')
}

function Write-GatewayLauncher($Config) {
    # tunnel-client 0.0.18 parses --mcp-command as whitespace-delimited words
    # on Windows, so quoting a gateway path containing spaces is not sufficient.
    # Keep its command target to a no-space .cmd path and let cmd.exe preserve
    # the original absolute paths when it starts Python.
    $launcherPath = Join-Path (Split-Path $Config.client) 'obsidian-mcp.cmd'
    if ($launcherPath -match '\s') { throw 'O caminho do runtime não pode conter espaços.' }
    $escape = { param([string]$Value) $Value.Replace('"', '""') }
    $content = "@echo off`r`n`"$(& $escape $Config.python)`" `"$(& $escape $Config.gateway)`"`r`n"
    Set-Content -LiteralPath $launcherPath -Value $content -Encoding ascii
    return $launcherPath.Replace('\', '/')
}

function Get-SafeStatusSummary([string]$Text) {
    try {
        $status = $Text | ConvertFrom-Json
        $issues = @($status.issues) + @($status.local.issues) | Where-Object { $_ }
        $summary = "process_running=$($status.process_running); healthy=$($status.healthy); ready=$($status.ready)"
        if ($issues.Count) { $summary += '; issues=' + ($issues -join ' | ') }
        return [regex]::Replace($summary, '(?i)(sk-|key_)[A-Za-z0-9_.-]+', '$1[REDACTED]')
    } catch {
        return 'status indisponível ou inválido'
    }
}

try {
    if ($Action -eq 'Install') {
        if (-not $ClientSource -or -not $PythonPath) { throw 'Informe ClientSource e PythonPath.' }
        $zip = Join-Path $ClientSource 'client.zip'
        if ((Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLowerInvariant() -ne
            '8d0da1ce79532d44ccc5ed5d8bd36cdfffba37dfd287c602d69635c8bb5db2b2') {
            throw 'O pacote oficial do cliente não corresponde ao hash verificado.'
        }
        $gatewayPath = Join-Path (Split-Path $PSScriptRoot) 'server/operation_gateway.py'
        if (-not (Test-Path -LiteralPath $gatewayPath)) { throw 'Gateway não encontrado.' }
        if (-not (Test-Path -LiteralPath $PythonPath)) { throw 'Python não encontrado.' }
        Protect-Directory $RuntimeRoot
        $bin = Join-Path $RuntimeRoot 'bin'
        New-Item -ItemType Directory -Path $bin -Force | Out-Null
        # Extract the verified archive, not mutable loose executables.
        Expand-Archive -LiteralPath $zip -DestinationPath $bin -Force
        $config = [ordered]@{
            client = Join-Path $bin 'tunnel-client.exe'
            python = [IO.Path]::GetFullPath($PythonPath)
            gateway = [IO.Path]::GetFullPath($gatewayPath)
            tunnel_id = 'tunnel_6adf20f8028c8191ac3a2d02fb08392f'
            profile_dir = Join-Path $RuntimeRoot 'profiles'
            launcher = $PSCommandPath
        }
        $config | ConvertTo-Json | Set-Content -LiteralPath $configFile -Encoding utf8
        Write-Host 'Configuração automática do Obsidian Vault Bridge'
        Write-Host 'A chave será criptografada pelo Windows para este usuário, fora do projeto.'
        Write-Host 'O túnel iniciará em segundo plano ao entrar no Windows. Cada operação terá um worker temporário.'
        $secureKey = Read-Host 'Cole a chave restrita do túnel (entrada oculta)' -AsSecureString
        try {
            if ($secureKey.Length -eq 0) { throw 'Chave vazia; instalação cancelada.' }
            $secureKey | ConvertFrom-SecureString | Set-Content -LiteralPath $keyFile -Encoding ascii
        } finally { $secureKey.Dispose() }
        $startArgs = @('-NoLogo','-NoProfile','-NonInteractive','-WindowStyle','Hidden','-File',
            ('"'+$PSCommandPath+'"'),'-Action','Start','-RuntimeRoot',('"'+$RuntimeRoot+'"'))
        Start-Process -FilePath $pwshPath -ArgumentList $startArgs -WindowStyle Hidden | Out-Null
        $ready = $false
        for ($attempt = 0; $attempt -lt 40; $attempt++) {
            Start-Sleep -Seconds 1
            if (Test-Path -LiteralPath $statusFile) {
                if (Is-Ready (Get-Content -Raw -LiteralPath $statusFile)) { $ready = $true; break }
            }
        }
        if (-not $ready) { throw 'O cliente não ficou pronto. Consulte setup-error.log no diretório local do runtime.' }
        $shell = New-Object -ComObject WScript.Shell
        $shortcut = $shell.CreateShortcut($startupFile)
        $shortcut.TargetPath = $pwshPath
        $shortcut.Arguments = '-NoLogo -NoProfile -NonInteractive -WindowStyle Hidden -File "' + $PSCommandPath + '" -Action Start -RuntimeRoot "' + $RuntimeRoot + '"'
        $shortcut.WorkingDirectory = Split-Path $PSCommandPath
        $shortcut.WindowStyle = 7
        $shortcut.Description = 'Conexão privada do Obsidian Vault Bridge em segundo plano'
        $shortcut.Save()
        Write-Host 'Ponte pronta em segundo plano. Inicialização automática configurada para este usuário.'
        exit 0
    }
    $config = Read-Config
    if ($Action -eq 'Status') {
        Write-Output (Read-RuntimeStatus $config)
        exit 0
    }
    if ($Action -in @('Stop','Disable')) {
        & $config.client runtimes stop $aliasName --json
        if ($Action -eq 'Disable' -and (Test-Path -LiteralPath $startupFile)) {
            Remove-Item -LiteralPath $startupFile
        }
        exit $LASTEXITCODE
    }
    # Start is idempotent; native supervision owns the daemon and its gateway.
    $userSid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    $mutex = [Threading.Mutex]::new($false, ('Local\ObsidianVaultBridge-' + $userSid))
    $locked = $false
    try {
        $locked = $mutex.WaitOne(0)
        if (-not $locked) { exit 0 }
        $currentStatus = Read-RuntimeStatus $config
        if (Is-Ready $currentStatus) { $currentStatus | Set-Content -LiteralPath $statusFile; exit 0 }
        $secureKey = (Get-Content -Raw -LiteralPath $keyFile).Trim() | ConvertTo-SecureString
        $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
        try { $env:CONTROL_PLANE_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
        finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer); $secureKey.Dispose() }
        try {
            $command = Write-GatewayLauncher $config
            $connectArgs = @('runtimes','connect','--alias',$aliasName,'--tunnel-id',$config.tunnel_id,
                '--runtime-api-key','env:CONTROL_PLANE_API_KEY','--mcp-command',$command,
                '--profile',$aliasName,'--profile-dir',$config.profile_dir,'--json')
            $null = & $config.client @connectArgs 2>&1
            if ($LASTEXITCODE -ne 0) { throw 'O cliente oficial não conseguiu iniciar a conexão gerenciada.' }
            for ($attempt = 0; $attempt -lt 25; $attempt++) {
                $currentStatus = Read-RuntimeStatus $config
                $currentStatus | Set-Content -LiteralPath $statusFile -Encoding utf8
                if (Is-Ready $currentStatus) { exit 0 }
                Start-Sleep -Seconds 1
            }
            throw ('Runtime iniciou, mas não ficou saudável/pronto em 25 segundos. ' + (Get-SafeStatusSummary $currentStatus) +
                '. Consulte o log local do tunnel-client para a causa.')
        } finally { Remove-Item Env:CONTROL_PLANE_API_KEY -ErrorAction SilentlyContinue }
    } finally {
        if ($locked) { $mutex.ReleaseMutex() }
        $mutex.Dispose()
    }
} catch {
    if (Test-Path -LiteralPath $RuntimeRoot) {
        $message = [regex]::Replace($_.Exception.Message, '(?i)(sk-|key_)[A-Za-z0-9_.-]+', '$1[REDACTED]')
        $message | Set-Content -LiteralPath (Join-Path $RuntimeRoot 'setup-error.log') -Encoding utf8
    }
    Write-Error 'Não foi possível configurar ou iniciar a ponte. A chave não é incluída no diagnóstico.'
    exit 1
}
