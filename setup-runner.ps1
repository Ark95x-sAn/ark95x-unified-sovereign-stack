#Requires -RunAsAdministrator
<#
.SYNOPSIS
    ARK95X Sovereign Stack - Self-Hosted GitHub Actions Runner Setup
    Deploys and configures a Windows self-hosted runner for CI/CD operations.

.DESCRIPTION
    This script:
    1. Downloads the GitHub Actions Runner for Windows x64
    2. Validates the package checksum
    3. Extracts and configures the runner
    4. Installs Docker Desktop prerequisites
    5. Registers the runner as a Windows service (auto-start on boot)
    6. Starts the runner service

.NOTES
    Run as Administrator in PowerShell.
    Runner token expires - get a fresh one from:
    https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/settings/actions/runners/new
#>

param(
    [string]$RunnerToken = "",
    [string]$RunnerName = "ARK95X-SOVEREIGN-$(hostname)",
    [string]$RunnerLabels = "self-hosted,Windows,X64,sovereign,ark95x",
    [string]$WorkDir = "C:\actions-runner",
    [string]$RepoUrl = "https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack",
    [switch]$InstallAsService
)

$ErrorActionPreference = "Stop"
$RunnerVersion = "2.332.0"
$RunnerZip = "actions-runner-win-x64-$RunnerVersion.zip"
$RunnerUrl = "https://github.com/actions/runner/releases/download/v$RunnerVersion/$RunnerZip"
$ExpectedHash = "83e56e05b21eb58c9697f82e52c53b30867335ff039cd5d44d1a1a24d2149f4b"

function Write-Banner {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "  ARK95X SOVEREIGN RUNNER DEPLOYMENT" -ForegroundColor Yellow
    Write-Host "  Self-Hosted GitHub Actions Runner" -ForegroundColor Yellow
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
}

function Test-Prerequisites {
    Write-Host "[CHECK] Verifying prerequisites..." -ForegroundColor Cyan

    # Check admin
    $isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        throw "This script must run as Administrator."
    }
    Write-Host "  [OK] Running as Administrator" -ForegroundColor Green

    # Check PowerShell version
    if ($PSVersionTable.PSVersion.Major -lt 5) {
        throw "PowerShell 5.1+ required. Current: $($PSVersionTable.PSVersion)"
    }
    Write-Host "  [OK] PowerShell $($PSVersionTable.PSVersion)" -ForegroundColor Green

    # Check .NET
    try {
        $dotnet = dotnet --version 2>$null
        Write-Host "  [OK] .NET SDK: $dotnet" -ForegroundColor Green
    } catch {
        Write-Host "  [WARN] .NET SDK not found - some features may be limited" -ForegroundColor Yellow
    }

    # Check Docker
    try {
        $docker = docker --version 2>$null
        Write-Host "  [OK] Docker: $docker" -ForegroundColor Green
    } catch {
        Write-Host "  [WARN] Docker not installed - required for deployment jobs" -ForegroundColor Yellow
        Write-Host "  [INFO] Install Docker Desktop from https://docker.com/products/docker-desktop" -ForegroundColor Gray
    }

    # Check Git
    try {
        $git = git --version 2>$null
        Write-Host "  [OK] Git: $git" -ForegroundColor Green
    } catch {
        throw "Git is required. Install from https://git-scm.com"
    }
}

function Install-Runner {
    Write-Host ""
    Write-Host "[DEPLOY] Installing GitHub Actions Runner v$RunnerVersion..." -ForegroundColor Cyan

    # Create directory
    if (-not (Test-Path $WorkDir)) {
        New-Item -ItemType Directory -Path $WorkDir -Force | Out-Null
    }
    Set-Location $WorkDir

    # Download
    $zipPath = Join-Path $WorkDir $RunnerZip
    if (-not (Test-Path $zipPath)) {
        Write-Host "  Downloading runner package..." -ForegroundColor Gray
        Invoke-WebRequest -Uri $RunnerUrl -OutFile $zipPath
        Write-Host "  [OK] Downloaded $RunnerZip" -ForegroundColor Green
    } else {
        Write-Host "  [OK] Runner package already exists" -ForegroundColor Green
    }

    # Validate hash
    $hash = (Get-FileHash -Path $zipPath -Algorithm SHA256).Hash.ToUpper()
    if ($hash -ne $ExpectedHash.ToUpper()) {
        Remove-Item $zipPath -Force
        throw "Checksum mismatch! Expected: $ExpectedHash Got: $hash"
    }
    Write-Host "  [OK] Checksum verified" -ForegroundColor Green

    # Extract
    if (-not (Test-Path (Join-Path $WorkDir "config.cmd"))) {
        Write-Host "  Extracting runner..." -ForegroundColor Gray
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [System.IO.Compression.ZipFile]::ExtractToDirectory($zipPath, $WorkDir)
        Write-Host "  [OK] Extracted to $WorkDir" -ForegroundColor Green
    } else {
        Write-Host "  [OK] Runner already extracted" -ForegroundColor Green
    }
}

function Register-Runner {
    Write-Host ""
    Write-Host "[CONFIG] Configuring runner..." -ForegroundColor Cyan

    if ([string]::IsNullOrEmpty($RunnerToken)) {
        Write-Host ""
        Write-Host "  TOKEN REQUIRED!" -ForegroundColor Red
        Write-Host "  Get a fresh token from:" -ForegroundColor Yellow
        Write-Host "  https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/settings/actions/runners/new" -ForegroundColor White
        Write-Host ""
        $RunnerToken = Read-Host "  Paste your runner registration token"
    }

    Set-Location $WorkDir

    # Configure
    $configArgs = @(
        "--url", $RepoUrl,
        "--token", $RunnerToken,
        "--name", $RunnerName,
        "--labels", $RunnerLabels,
        "--work", "_work",
        "--runasservice"
    )

    Write-Host "  Runner Name: $RunnerName" -ForegroundColor White
    Write-Host "  Labels: $RunnerLabels" -ForegroundColor White
    Write-Host "  Repo: $RepoUrl" -ForegroundColor White
    Write-Host ""

    & "$WorkDir\config.cmd" @configArgs

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Runner registered successfully" -ForegroundColor Green
    } else {
        throw "Runner configuration failed with exit code $LASTEXITCODE"
    }
}

function Install-RunnerService {
    Write-Host ""
    Write-Host "[SERVICE] Installing runner as Windows service..." -ForegroundColor Cyan

    Set-Location $WorkDir

    # Install service
    & "$WorkDir\svc.cmd" install

    # Start service
    & "$WorkDir\svc.cmd" start

    # Verify
    $svc = Get-Service -Name "actions.runner.*" -ErrorAction SilentlyContinue
    if ($svc -and $svc.Status -eq "Running") {
        Write-Host "  [OK] Runner service installed and running" -ForegroundColor Green
        Write-Host "  Service: $($svc.Name)" -ForegroundColor White
        Write-Host "  Status: $($svc.Status)" -ForegroundColor White
    } else {
        Write-Host "  [WARN] Service may need manual start" -ForegroundColor Yellow
        Write-Host "  Run: $WorkDir\svc.cmd start" -ForegroundColor Gray
    }
}

function Show-Summary {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "  SOVEREIGN RUNNER DEPLOYMENT COMPLETE" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Runner: $RunnerName" -ForegroundColor White
    Write-Host "  Location: $WorkDir" -ForegroundColor White
    Write-Host "  Labels: $RunnerLabels" -ForegroundColor White
    Write-Host ""
    Write-Host "  COMMANDS:" -ForegroundColor Yellow
    Write-Host "    Manual run:    $WorkDir\run.cmd" -ForegroundColor Gray
    Write-Host "    Start svc:     $WorkDir\svc.cmd start" -ForegroundColor Gray
    Write-Host "    Stop svc:      $WorkDir\svc.cmd stop" -ForegroundColor Gray
    Write-Host "    Check status:  Get-Service actions.runner.*" -ForegroundColor Gray
    Write-Host "    Remove runner: $WorkDir\config.cmd remove --token <TOKEN>" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  The deploy pipeline will now auto-execute when" -ForegroundColor Cyan
    Write-Host "  you push to main. Your runner picks up the job." -ForegroundColor Cyan
    Write-Host ""
}

# === MAIN EXECUTION ===
Write-Banner
Test-Prerequisites
Install-Runner
Register-Runner
Install-RunnerService
Show-Summary
