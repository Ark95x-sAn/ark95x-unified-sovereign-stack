param(
    [string]$Repo = "Ark95x-sAn/ark95x-unified-sovereign-stack",
    [int]$IssueNumber = 34,
    [string]$N95Root = "C:\N95\n95-demand-memory-engine",
    [string]$RTXAddress = "192.168.1.52",
    [string]$GM700Address = "192.168.1.51"
)

$ErrorActionPreference = "Stop"
$MissionId = "N95-DEPLOY-SPINE-20260905"
$ExpectedAuthor = "Ark95x-sAn"
$ExpectedAction = "DEPLOY_RTX"
$ExpectedTarget = "RTX2080_AI_NODE"
$ExpectedDimensions = 768
$ExpectedModel = "nomic-embed-text"

function Stop-Hold([string]$Reason) {
    $stamp = (Get-Date).ToString("o")
    $receipt = @{
        schema = "n95-executor-receipt/1.0"
        mission_id = $MissionId
        target = $ExpectedTarget
        executor = $env:COMPUTERNAME
        observed_at = $stamp
        state = "HOLD_REPAIR"
        reason = $Reason
    } | ConvertTo-Json -Depth 5
    try { gh issue comment $IssueNumber --repo $Repo --body "``````json`n$receipt`n``````" | Out-Null } catch {}
    Write-Error $Reason
    exit 2
}

# GitHub is the authenticated relay. No PAT or secret is stored in this script.
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Stop-Hold "GitHub CLI (gh) is not installed on the RTX node."
}

gh auth status 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Stop-Hold "GitHub CLI is not authenticated on the RTX node."
}

$issueRaw = gh issue view $IssueNumber --repo $Repo --json number,title,body,author,state
if ($LASTEXITCODE -ne 0) { Stop-Hold "Unable to read executor command issue #$IssueNumber." }
$issue = $issueRaw | ConvertFrom-Json

if ($issue.state -ne "OPEN") { Stop-Hold "Executor issue is not open." }
if ($issue.author.login -ne $ExpectedAuthor) { Stop-Hold "Executor issue author is not the expected repository owner." }
if ($issue.title -ne "[N95 EXEC] RTX2080 deployment command") { Stop-Hold "Executor issue title mismatch." }

$required = @(
    "N95_EXEC_COMMAND_V1",
    "mission_id: $MissionId",
    "target: $ExpectedTarget",
    "action: $ExpectedAction",
    "expected_status: RTX_EMBEDDING_NODE_READY",
    "expected_model: $ExpectedModel",
    "expected_embedding_dimensions: $ExpectedDimensions",
    "state: READY_FOR_AUTHENTICATED_RTX_EXECUTOR"
)
foreach ($line in $required) {
    if ($issue.body -notmatch [regex]::Escape($line)) { Stop-Hold "Command contract mismatch: missing '$line'." }
}

# Refuse to run on a machine that does not actually report an RTX 2080-class GPU.
if (-not (Get-Command nvidia-smi.exe -ErrorAction SilentlyContinue)) {
    Stop-Hold "nvidia-smi is unavailable; target GPU identity cannot be checked."
}
$gpuNames = (& nvidia-smi.exe --query-gpu=name --format=csv,noheader 2>$null) -join "; "
if ($gpuNames -notmatch "RTX\s*2080") {
    Stop-Hold "Target identity check failed. Observed GPU(s): $gpuNames"
}

$deployer = Join-Path $N95Root "infra\rtx2080\deploy-rtx2080.ps1"
if (-not (Test-Path $deployer)) { Stop-Hold "Existing RTX deployer not found at $deployer" }

$receiptDir = Join-Path $N95Root "out\executor"
New-Item -ItemType Directory -Path $receiptDir -Force | Out-Null
$runId = "RTX-" + (Get-Date -Format "yyyyMMdd-HHmmss")
$logPath = Join-Path $receiptDir "$runId.log"
$receiptPath = Join-Path $receiptDir "$runId.receipt.json"

$started = Get-Date
$exitCode = 0
try {
    Set-ExecutionPolicy -Scope Process Bypass -Force
    & $deployer `
        -BindAddress $RTXAddress `
        -GM700Address $GM700Address `
        -InstallOllama `
        -RestartOllama `
        -OpenFirewall *>&1 | Tee-Object -FilePath $logPath
    if ($LASTEXITCODE) { $exitCode = $LASTEXITCODE }
} catch {
    $_ | Out-String | Add-Content -Path $logPath
    $exitCode = 1
}

if ($exitCode -ne 0) { Stop-Hold "RTX deployer exited with code $exitCode. Log: $logPath" }

# Independent postcondition: query the running Ollama embedding endpoint and count dimensions.
try {
    $payload = @{ model = $ExpectedModel; input = "network95 executor verification" } | ConvertTo-Json -Compress
    $embed = Invoke-RestMethod -Method Post -Uri "http://${RTXAddress}:11434/api/embed" -ContentType "application/json" -Body $payload -TimeoutSec 60
} catch {
    Stop-Hold "RTX deployer completed but /api/embed could not be verified: $($_.Exception.Message)"
}

$dimensions = 0
if ($embed.embeddings -and $embed.embeddings.Count -gt 0) {
    $dimensions = $embed.embeddings[0].Count
} elseif ($embed.embedding) {
    $dimensions = $embed.embedding.Count
}

$status = if ($dimensions -eq $ExpectedDimensions) { "RTX_EMBEDDING_NODE_READY" } else { "HOLD_REPAIR" }
$finished = Get-Date
$logHash = (Get-FileHash -Algorithm SHA256 -Path $logPath).Hash.ToLowerInvariant()

$receiptObj = [ordered]@{
    schema = "n95-executor-receipt/1.0"
    mission_id = $MissionId
    command_issue = $IssueNumber
    target = $ExpectedTarget
    executor_computer = $env:COMPUTERNAME
    executor_user = $env:USERNAME
    gpu = $gpuNames
    started_at = $started.ToString("o")
    finished_at = $finished.ToString("o")
    action = $ExpectedAction
    deployer = $deployer
    deployer_exit_code = $exitCode
    status = $status
    model = $ExpectedModel
    embedding_dimensions = $dimensions
    expected_embedding_dimensions = $ExpectedDimensions
    log_path = $logPath
    log_sha256 = $logHash
}
$receiptJson = $receiptObj | ConvertTo-Json -Depth 6
$receiptJson | Set-Content -Path $receiptPath -Encoding UTF8

gh issue comment $IssueNumber --repo $Repo --body "RTX machine receipt:`n`n``````json`n$receiptJson`n``````" | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Receipt was written locally but could not be posted to GitHub: $receiptPath"
    exit 3
}

if ($status -ne "RTX_EMBEDDING_NODE_READY") {
    Write-Host $receiptJson
    exit 2
}

Write-Host $receiptJson
Write-Host "RTX_EXECUTOR_RECEIPT_POSTED" -ForegroundColor Green
exit 0
