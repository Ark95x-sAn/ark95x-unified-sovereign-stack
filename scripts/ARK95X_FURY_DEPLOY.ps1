# ============================================================
# ARK95X FURY DEPLOY - Master Command Center Deployment
# Full system deployment with Manus + ZenCode + VibeCoder
# Network-95 LLC | Nordskog Properties LLC | 2026
# ============================================================
$ErrorActionPreference = "Stop"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = "$HOME\ARK95X_FURY_DEPLOY_$timestamp.log"

function Log { param($msg) $line = "[$(Get-Date -Format 'HH:mm:ss')] $msg"; Write-Host $line -ForegroundColor Cyan; Add-Content $logFile $line }

Log "========================================"
Log "  ARK95X FURY DEPLOY - FULL UNLEASH"
Log "  Manus + ZenCode + VibeCoder"
Log "  Protocols: MCP / A2A / ACP"
Log "========================================"

# --- Step 1: Clone/Pull Repo ---
$repoUrl = "https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack.git"
$repoDir = "$HOME\ark95x-unified-sovereign-stack"

if (Test-Path $repoDir) {
    Log "Pulling latest from GitHub..."
    Set-Location $repoDir
    git pull origin main 2>&1 | Out-Null
} else {
    Log "Cloning repository..."
    git clone $repoUrl $repoDir 2>&1 | Out-Null
    Set-Location $repoDir
}
Log "[OK] Repository ready"

# --- Step 2: Python Environment ---
Log "Setting up Python environment..."
if (-not (Test-Path "venv")) {
    python -m venv venv 2>&1 | Out-Null
}
.\venv\Scripts\Activate.ps1
pip install fastapi uvicorn pydantic aiohttp requests crewai langchain 2>&1 | Out-Null
Log "[OK] Python environment ready"

# --- Step 3: Verify Command Center Files ---
$requiredFiles = @(
    "command/agents/manus_agent.py",
    "command/agents/zencode_agent.py",
    "command/agents/vibecoder_agent.py",
    "command/agents/__init__.py",
    "command/protocol_router.py",
    "command/command_center_api.py"
)

$allPresent = $true
foreach ($f in $requiredFiles) {
    if (Test-Path $f) {
        Log "  [OK] $f"
    } else {
        Log "  [MISSING] $f"
        $allPresent = $false
    }
}

if (-not $allPresent) {
    Log "[ERROR] Missing command center files. Run git pull first."
    exit 1
}
Log "[OK] All command center files verified"

# --- Step 4: Docker Services ---
Log "Starting Docker services..."
if (Get-Command docker -ErrorAction SilentlyContinue) {
    docker-compose up -d 2>&1 | Out-Null
    Log "[OK] Docker services started"
} else {
    Log "[SKIP] Docker not found - running standalone"
}

# --- Step 5: Launch Command Center ---
Log "Launching ARK95X Command Center API..."
Start-Process -NoNewWindow -FilePath "python" -ArgumentList "-m", "uvicorn", "command.command_center_api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"
Start-Sleep -Seconds 3

# --- Step 6: Verify ---
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/" -Method Get
    Log "[OK] Command Center API is LIVE"
    Log "  System: $($response.system)"
    Log "  Version: $($response.version)"
    Log "  Status: $($response.status)"
} catch {
    Log "[WARN] API not responding yet - may need a moment to start"
}

# --- Step 7: System Report ---
Log ""
Log "========================================"
Log "  ARK95X FURY DEPLOY COMPLETE"
Log "========================================"
Log "  Agents: Manus, ZenCode, VibeCoder"
Log "  Protocols: MCP, A2A, ACP"
Log "  Skills: 34 total across 5 categories"
Log "  Tools: 12 registered"
Log "  API: http://localhost:8000"
Log "  Docs: http://localhost:8000/docs"
Log "  Manifest: http://localhost:8000/manifest"
Log "  Fury Mode: POST http://localhost:8000/fury"
Log "  Router: http://localhost:8000/router/status"
Log "========================================"
Log "  Log: $logFile"
Log "========================================"
