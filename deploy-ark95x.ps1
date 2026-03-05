<#
.SYNOPSIS
    ARK95X Unified Sovereign Stack - Windows Deployment Script
.DESCRIPTION
    Complete deployment automation for ark95x-unified-sovereign-stack with Docker Compose orchestration
.NOTES
    Author: ARK95X System
    Version: 1.0.0
    Date: 2026-03-05
#>

#Requires -Version 5.1
#Requires -RunAsAdministrator

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$InstallDir = "$env:USERPROFILE\ark95x-stack",

    [Parameter(Mandatory=$false)]
    [string]$RepoUrl = "https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack.git",

    [Parameter(Mandatory=$false)]
    [switch]$SkipPrereqCheck,

    [Parameter(Mandatory=$false)]
    [switch]$CleanInstall
)

$ErrorActionPreference = "Stop"
$Script:LogFile = Join-Path $env:TEMP "ark95x-deploy-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"
$Script:DeploymentStartTime = Get-Date
$Script:ServicesHealthy = $false

$Script:OllamaModels = @("llama3", "deepseek-r1", "codellama")
$Script:RequiredPorts = @(8000, 5432, 6379, 27017, 6333, 5678, 8080, 11434)
$Script:ServiceEndpoints = @{
    "ARK95X Core" = "http://localhost:8000"
    "PostgreSQL" = "localhost:5432"
    "Redis" = "localhost:6379"
    "MongoDB" = "localhost:27017"
    "Qdrant" = "http://localhost:6333"
    "n8n" = "http://localhost:5678"
    "SearXNG" = "http://localhost:8080"
    "Ollama" = "http://localhost:11434"
}

# LOGGING FUNCTIONS
function Write-ColorOutput {
    param([string]$Message, [string]$Type = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Type] $Message"
    Add-Content -Path $Script:LogFile -Value $logMessage
    switch ($Type) {
        "SUCCESS" { Write-Host "+ $Message" -ForegroundColor Green }
        "ERROR" { Write-Host "x $Message" -ForegroundColor Red }
        "WARNING" { Write-Host "! $Message" -ForegroundColor Yellow }
        "INFO" { Write-Host "> $Message" -ForegroundColor Cyan }
        "HEADER" { Write-Host "`n$Message" -ForegroundColor Magenta }
        "DETAIL" { Write-Host "  $Message" -ForegroundColor Gray }
        default { Write-Host $Message }
    }
}

function Write-Banner {
    $banner = @"
    ========================================================
    =   ARK95X UNIFIED SOVEREIGN STACK DEPLOYER            =
    =   Quantum-Grade Multi-Agent Infrastructure System     =
    ========================================================
"@
    Write-Host $banner -ForegroundColor Cyan
    Write-ColorOutput "Deployment Log: $Script:LogFile" -Type "INFO"
}

# PREREQUISITE CHECKS
function Test-Prerequisites {
    Write-ColorOutput "PREREQUISITE VERIFICATION" -Type "HEADER"
    $allChecks = $true
    try { $gitVersion = git --version 2>&1; if ($LASTEXITCODE -eq 0) { Write-ColorOutput "Git: $gitVersion" -Type "SUCCESS" } else { throw } } catch { Write-ColorOutput "Git not found" -Type "ERROR"; $allChecks = $false }
    try { $dockerVersion = docker --version 2>&1; if ($LASTEXITCODE -eq 0) { Write-ColorOutput "Docker: $dockerVersion" -Type "SUCCESS"; $dockerInfo = docker info 2>&1; if ($LASTEXITCODE -ne 0) { Write-ColorOutput "Docker not running" -Type "ERROR"; $allChecks = $false } } else { throw } } catch { Write-ColorOutput "Docker not found" -Type "ERROR"; $allChecks = $false }
    try { $composeVersion = docker compose version 2>&1; if ($LASTEXITCODE -eq 0) { Write-ColorOutput "Compose: $composeVersion" -Type "SUCCESS" } else { throw } } catch { Write-ColorOutput "Docker Compose not available" -Type "ERROR"; $allChecks = $false }
    try { $pythonVersion = python --version 2>&1; Write-ColorOutput "Python: $pythonVersion" -Type "SUCCESS" } catch { Write-ColorOutput "Python not found" -Type "WARNING" }
    try { $nodeVersion = node --version 2>&1; Write-ColorOutput "Node.js: $nodeVersion" -Type "SUCCESS" } catch { Write-ColorOutput "Node.js not found" -Type "WARNING" }
    try { $ollamaVersion = ollama --version 2>&1; Write-ColorOutput "Ollama: $ollamaVersion" -Type "SUCCESS" } catch { Write-ColorOutput "Ollama not found" -Type "WARNING" }
    foreach ($port in $Script:RequiredPorts) { $conn = Test-NetConnection -ComputerName localhost -Port $port -WarningAction SilentlyContinue -ErrorAction SilentlyContinue; if ($conn.TcpTestSucceeded) { Write-ColorOutput "Port $port in use" -Type "WARNING" } }
    $drive = $env:USERPROFILE.Substring(0, 1); $freeSpace = (Get-PSDrive $drive).Free / 1GB
    if ($freeSpace -gt 20) { Write-ColorOutput "Disk: $([math]::Round($freeSpace, 2)) GB free" -Type "SUCCESS" } else { Write-ColorOutput "Low disk: $([math]::Round($freeSpace, 2)) GB" -Type "WARNING" }
    if (-not $allChecks) { throw "Prerequisites failed" }
}

# REPOSITORY MANAGEMENT
function Initialize-Repository {
    Write-ColorOutput "REPOSITORY INITIALIZATION" -Type "HEADER"
    if ($CleanInstall -and (Test-Path $InstallDir)) { Remove-Item -Path $InstallDir -Recurse -Force }
    if (Test-Path $InstallDir) {
        Set-Location $InstallDir; git fetch --all 2>&1 | Out-Null; git reset --hard origin/main 2>&1 | Out-Null
        Write-ColorOutput "Repository updated" -Type "SUCCESS"
    } else {
        git clone $RepoUrl $InstallDir 2>&1 | ForEach-Object { Write-ColorOutput $_ -Type "DETAIL" }
        Write-ColorOutput "Repository cloned" -Type "SUCCESS"; Set-Location $InstallDir
    }
}

# ENVIRONMENT CONFIGURATION
function Initialize-Environment {
    Write-ColorOutput "ENVIRONMENT CONFIGURATION" -Type "HEADER"
    $envFile = Join-Path $InstallDir ".env"
    if (Test-Path $envFile) { $r = Read-Host "Overwrite .env? (y/N)"; if ($r -ne 'y') { return } }
    $postgresPassword = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
    $envContent = @"
OPENAI_API_KEY=sk-your-key-here
OLLAMA_HOST=http://host.docker.internal:11434
POSTGRES_PASSWORD=$postgresPassword
POSTGRES_URL=postgresql://ark95x:${postgresPassword}@postgres:5432/sovereign
MONGODB_URL=mongodb://mongodb:27017/ark95x
REDIS_URL=redis://redis:6379
QDRANT_URL=http://qdrant:6333
SEARXNG_URL=http://searxng:8080
N8N_URL=http://n8n:5678
TRADING_MODE=paper
APP_ENV=development
APP_PORT=8000
LOG_LEVEL=INFO
"@
    Set-Content -Path $envFile -Value $envContent -Encoding UTF8
    Write-ColorOutput ".env generated" -Type "SUCCESS"
}

# DOCKER ORCHESTRATION
function Start-DockerStack {
    Write-ColorOutput "DOCKER STACK DEPLOYMENT" -Type "HEADER"
    try {
        docker compose pull 2>&1 | ForEach-Object { if ($_ -match "Pulling|Downloaded") { Write-ColorOutput $_ -Type "DETAIL" } }
        docker compose build --no-cache 2>&1 | ForEach-Object { if ($_ -match "Step|Successfully") { Write-ColorOutput $_ -Type "DETAIL" } }
        docker compose up -d 2>&1 | ForEach-Object { Write-ColorOutput $_ -Type "DETAIL" }
        Write-ColorOutput "All services started" -Type "SUCCESS"
    } catch { Write-ColorOutput "Docker failed: $_" -Type "ERROR"; Invoke-Rollback; throw }
}

# HEALTH CHECKS
function Test-ServiceHealth {
    Write-ColorOutput "SERVICE HEALTH VERIFICATION" -Type "HEADER"
    Start-Sleep -Seconds 30
    $healthStatus = @{}
    foreach ($endpoint in $Script:ServiceEndpoints.Keys) {
        $url = $Script:ServiceEndpoints[$endpoint]
        if ($url -match "^http") {
            try { $response = Invoke-WebRequest -Uri $url -Method Get -TimeoutSec 5 -ErrorAction Stop; Write-ColorOutput "$endpoint responding (HTTP $($response.StatusCode))" -Type "SUCCESS"; $healthStatus[$endpoint] = $true }
            catch { Write-ColorOutput "$endpoint not responding" -Type "WARNING"; $healthStatus[$endpoint] = $false }
        } else {
            $port = $url -replace ".*:", ""; $conn = Test-NetConnection -ComputerName localhost -Port $port -WarningAction SilentlyContinue
            if ($conn.TcpTestSucceeded) { Write-ColorOutput "$endpoint on port $port" -Type "SUCCESS"; $healthStatus[$endpoint] = $true }
            else { Write-ColorOutput "$endpoint not on port $port" -Type "WARNING"; $healthStatus[$endpoint] = $false }
        }
    }
    $healthy = ($healthStatus.Values | Where-Object { $_ -eq $true }).Count
    if ($healthy -eq $healthStatus.Count) { $Script:ServicesHealthy = $true }
    return $healthStatus
}

# OLLAMA MODELS
function Install-OllamaModels {
    Write-ColorOutput "OLLAMA MODEL DEPLOYMENT" -Type "HEADER"
    try { Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 5 -ErrorAction Stop } catch { Write-ColorOutput "Ollama not available, skipping" -Type "WARNING"; return }
    foreach ($model in $Script:OllamaModels) {
        Write-ColorOutput "Pulling $model..." -Type "INFO"
        try { Start-Process -FilePath "ollama" -ArgumentList "pull", $model -NoNewWindow -PassThru -Wait | Out-Null; Write-ColorOutput "$model installed" -Type "SUCCESS" }
        catch { Write-ColorOutput "$model failed" -Type "ERROR" }
    }
}

# STATUS DASHBOARD
function Show-StatusDashboard {
    param([hashtable]$HealthStatus)
    Write-ColorOutput "DEPLOYMENT STATUS DASHBOARD" -Type "HEADER"
    $deployTime = (Get-Date) - $Script:DeploymentStartTime
    Write-Host "`n====== SERVICE STATUS ======" -ForegroundColor Cyan
    foreach ($svc in $Script:ServiceEndpoints.Keys) {
        $st = if ($HealthStatus[$svc]) { "HEALTHY" } else { "DEGRADED" }; $c = if ($HealthStatus[$svc]) { "Green" } else { "Red" }
        Write-Host "  $svc : $st ($($Script:ServiceEndpoints[$svc]))" -ForegroundColor $c
    }
    Write-Host "`n  Deploy Time: $([math]::Round($deployTime.TotalSeconds, 2))s" -ForegroundColor White
    Write-Host "  Log: $Script:LogFile" -ForegroundColor White
    Write-Host "`n====== QUICK ACCESS ======" -ForegroundColor Cyan
    Write-Host "  Core API: http://localhost:8000" -ForegroundColor White
    Write-Host "  n8n: http://localhost:5678" -ForegroundColor White
    Write-Host "  Qdrant: http://localhost:6333" -ForegroundColor White
    Write-Host "  SearXNG: http://localhost:8080" -ForegroundColor White
    if ($Script:ServicesHealthy) { Write-ColorOutput "ARK95X STACK DEPLOYED SUCCESSFULLY" -Type "SUCCESS" }
    else { Write-ColorOutput "Stack deployed with warnings" -Type "WARNING" }
}

# ROLLBACK
function Invoke-Rollback {
    Write-ColorOutput "INITIATING ROLLBACK" -Type "WARNING"
    try { docker compose down --volumes 2>&1 | Out-Null; Write-ColorOutput "Containers stopped" -Type "SUCCESS" } catch { Write-ColorOutput "Rollback failed: $_" -Type "ERROR" }
}

# MAIN EXECUTION
function Start-Deployment {
    try {
        Write-Banner
        if (-not $SkipPrereqCheck) { Test-Prerequisites }
        Initialize-Repository
        Initialize-Environment
        Start-DockerStack
        $healthStatus = Test-ServiceHealth
        Install-OllamaModels
        Show-StatusDashboard -HealthStatus $healthStatus
    } catch {
        Write-ColorOutput "DEPLOYMENT FAILED: $_" -Type "ERROR"
        $choice = Read-Host "Rollback? (Y/n)"
        if ($choice -ne 'n') { Invoke-Rollback }
        exit 1
    }
}

Start-Deployment
