#Requires -RunAsAdministrator
<#
.SYNOPSIS
    ARK95X Unified Sovereign Stack - One-Click Windows Installer
.DESCRIPTION
    Clones repo, configures environment, pulls Docker images, and starts the full stack.
    Run: powershell -ExecutionPolicy Bypass -File install.ps1
#>

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$REPO_URL = 'https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack.git'
$INSTALL_DIR = "$env:USERPROFILE\ark95x-unified-sovereign-stack"
$LOG_FILE = "$INSTALL_DIR\install-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

function Write-Banner {
    Write-Host @"

    =====================================================
     ARK95X UNIFIED SOVEREIGN STACK - INSTALLER
     All repositories. One united front.
    =====================================================

"@ -ForegroundColor Cyan
}

function Log($msg) {
    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $line = "[$ts] $msg"
    Write-Host $line
    if (Test-Path (Split-Path $LOG_FILE)) { $line | Out-File -Append $LOG_FILE }
}

function Test-Command($cmd) {
    return [bool](Get-Command $cmd -ErrorAction SilentlyContinue)
}

function Install-Prerequisites {
    Log 'Checking prerequisites...'

    # Docker Desktop
    if (-not (Test-Command 'docker')) {
        Log 'Docker not found. Installing Docker Desktop...'
        $dockerUrl = 'https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe'
        $dockerInstaller = "$env:TEMP\DockerDesktopInstaller.exe"
        Invoke-WebRequest -Uri $dockerUrl -OutFile $dockerInstaller
        Start-Process -Wait -FilePath $dockerInstaller -ArgumentList 'install', '--quiet', '--accept-license'
        Log 'Docker Desktop installed. You may need to restart and re-run this script.'
    } else {
        $dockerVersion = docker --version
        Log "Docker found: $dockerVersion"
    }

    # Docker Compose
    if (-not (Test-Command 'docker-compose')) {
        Log 'docker-compose not found, checking Docker Compose V2...'
        $composeCheck = docker compose version 2>$null
        if ($composeCheck) {
            Log "Docker Compose V2: $composeCheck"
        } else {
            Log 'ERROR: Docker Compose not available'
            exit 1
        }
    }

    # Git
    if (-not (Test-Command 'git')) {
        Log 'Git not found. Installing via winget...'
        winget install --id Git.Git -e --silent
        $env:PATH += ";$env:ProgramFiles\Git\bin"
        Log 'Git installed'
    } else {
        Log "Git found: $(git --version)"
    }

    # Ollama
    if (-not (Test-Command 'ollama')) {
        Log 'Ollama not found. Installing...'
        Invoke-WebRequest -Uri 'https://ollama.ai/download/windows' -OutFile "$env:TEMP\ollama-setup.exe"
        Start-Process -Wait -FilePath "$env:TEMP\ollama-setup.exe" -ArgumentList '/S'
        Log 'Ollama installed'
    } else {
        Log "Ollama found: $(ollama --version 2>$null)"
    }

    # Check Docker running
    try {
        docker info | Out-Null
        Log 'Docker daemon is running'
    } catch {
        Log 'Starting Docker Desktop...'
        Start-Process 'C:\Program Files\Docker\Docker\Docker Desktop.exe'
        Log 'Waiting 30s for Docker to start...'
        Start-Sleep -Seconds 30
        docker info | Out-Null
        Log 'Docker daemon ready'
    }

    Log 'All prerequisites OK'
}

function Clone-Repository {
    Log 'Setting up repository...'
    if (Test-Path "$INSTALL_DIR\.git") {
        Log 'Repo exists, pulling latest...'
        Set-Location $INSTALL_DIR
        git pull origin main
    } else {
        Log "Cloning $REPO_URL..."
        git clone $REPO_URL $INSTALL_DIR
        Set-Location $INSTALL_DIR
    }
    Log "Repository ready at $INSTALL_DIR"
}

function Setup-Environment {
    Log 'Configuring environment...'
    $envFile = "$INSTALL_DIR\.env"

    if (Test-Path $envFile) {
        $backup = "$envFile.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        Copy-Item $envFile $backup
        Log "Backed up existing .env to $backup"
    }

    $pgPass = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 25 | ForEach-Object {[char]$_})
    $n8nKey = -join ((48..57) + (97..102) | Get-Random -Count 64 | ForEach-Object {[char]$_})

    @"
APP_ENV=production
APP_PORT=8000
LOG_LEVEL=INFO
POSTGRES_PASSWORD=$pgPass
OPENAI_API_KEY=
DEEPSEEK_API_KEY=
N8N_API_KEY=$n8nKey
GRAFANA_PASSWORD=ark95x_admin
"@ | Out-File -Encoding utf8 $envFile

    Log '.env configured (edit to add API keys)'
}

function Pull-OllamaModels {
    Log 'Pulling Ollama models...'
    $models = @('llama3', 'deepseek-r1', 'codellama')
    foreach ($m in $models) {
        $exists = ollama list 2>$null | Select-String "^$m"
        if (-not $exists) {
            Log "Pulling $m..."
            ollama pull $m
        } else {
            Log "Model $m already exists"
        }
        Log "Model ready: $m"
    }
}

function Deploy-Stack {
    Log 'Building and deploying Docker stack...'
    Set-Location $INSTALL_DIR

    Log 'Building images...'
    docker-compose build --no-cache 2>&1 | Tee-Object -Append $LOG_FILE

    Log 'Starting services...'
    docker-compose up -d 2>&1 | Tee-Object -Append $LOG_FILE

    Log 'Stack deployed. Waiting for services to start...'
    Start-Sleep -Seconds 20

    Log 'Container status:'
    docker-compose ps
}

function Test-Health {
    Log 'Running health checks...'
    $endpoints = @{
        'Core API'   = 'http://localhost:8000/health'
        'n8n'        = 'http://localhost:5678'
        'Qdrant'     = 'http://localhost:6333'
        'Ollama'     = 'http://localhost:11434/api/tags'
        'Grafana'    = 'http://localhost:3000'
        'Prometheus'  = 'http://localhost:9090'
    }

    $maxRetries = 5
    foreach ($svc in $endpoints.Keys) {
        $ok = $false
        for ($i = 1; $i -le $maxRetries; $i++) {
            try {
                $r = Invoke-WebRequest -Uri $endpoints[$svc] -TimeoutSec 5 -UseBasicParsing
                if ($r.StatusCode -lt 400) { Log "  [OK] $svc"; $ok = $true; break }
            } catch { Start-Sleep -Seconds 5 }
        }
        if (-not $ok) { Log "  [FAIL] $svc - $($endpoints[$svc])" }
    }
}

function Show-Dashboard {
    Write-Host @"

    =====================================================
     ARK95X SOVEREIGN STACK - DEPLOYMENT COMPLETE
    =====================================================

     Core API     : http://localhost:8000
     API Docs     : http://localhost:8000/docs
     Health Check : http://localhost:8000/health
     n8n Workflows: http://localhost:5678
     Qdrant       : http://localhost:6333
     SearXNG      : http://localhost:8080
     Prometheus   : http://localhost:9090
     Grafana      : http://localhost:3000 (admin/ark95x_admin)
     Ollama       : http://localhost:11434

     Install Dir  : $INSTALL_DIR
     Log File     : $LOG_FILE

     Commands:
       docker-compose ps           # View containers
       docker-compose logs -f      # Stream logs
       docker-compose restart      # Restart all
       docker-compose down         # Stop all

    =====================================================
"@ -ForegroundColor Green
}

# Main
Write-Banner
Log 'ARK95X Unified Sovereign Stack installer starting...'
Log "Timestamp: $(Get-Date)"
Log "Machine: $env:COMPUTERNAME"
Log "User: $env:USERNAME"

Install-Prerequisites
Clone-Repository
Setup-Environment
Pull-OllamaModels
Deploy-Stack
Test-Health
Show-Dashboard

Log 'Installation complete!'
