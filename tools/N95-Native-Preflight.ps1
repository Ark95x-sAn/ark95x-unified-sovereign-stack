#requires -Version 5.1
<#
.SYNOPSIS
Audits local Network-95 prerequisites and writes one local JSON receipt.
.DESCRIPTION
No installation, configuration changes, remote discovery, model execution, or
model downloads. Role is an operator assertion, not authenticated device identity.
The only network request is optional GET http://127.0.0.1:11434/api/tags on RTX2080.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('GM700', 'RTX2080', 'SURFACE')]
    [string]$Role,

    [string]$OutputDirectory
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

function Get-N95LocalApplication {
    param([string[]]$Names, [string[]]$Fallbacks = @())
    $paths = @()
    foreach ($name in $Names) {
        $commands = @(Get-Command -Name $name -CommandType Application -ErrorAction SilentlyContinue)
        foreach ($command in $commands) { $paths += $command.Source }
    }
    $paths += $Fallbacks
    foreach ($path in @($paths | Select-Object -Unique)) {
        if ([string]::IsNullOrWhiteSpace($path)) { continue }
        # Do not invoke Windows Store execution aliases or network executables.
        if ($path -notmatch '^[A-Za-z]:[\\/]' -or
            $path -match '\\Microsoft\\WindowsApps\\(python3?|py)\.exe$') { continue }
        try {
            $commandDrive = [System.IO.DriveInfo]::new([System.IO.Path]::GetPathRoot($path))
            if ($commandDrive.DriveType -eq [System.IO.DriveType]::Network) { continue }
            if (Test-Path -LiteralPath $path -PathType Leaf) { $path }
        }
        catch { }
    }
}

function Invoke-N95VersionProbe {
    param([string]$Executable, [string]$Arguments, [string]$Pattern)
    $result = [ordered]@{ verified = $false; version = $null; status = 'UNKNOWN' }
    $process = $null
    try {
        $startInfo = New-Object System.Diagnostics.ProcessStartInfo
        $startInfo.FileName = $Executable
        $startInfo.Arguments = $Arguments
        $startInfo.UseShellExecute = $false
        $startInfo.CreateNoWindow = $true
        $startInfo.RedirectStandardOutput = $true
        $startInfo.RedirectStandardError = $true
        $process = New-Object System.Diagnostics.Process
        $process.StartInfo = $startInfo
        if (-not $process.Start()) { throw 'VERSION_PROCESS_NOT_STARTED' }
        $stdoutTask = $process.StandardOutput.ReadToEndAsync()
        $stderrTask = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit(3000)) {
            # Stop only the version-probe process created immediately above.
            $process.Kill()
            $result.status = 'VERSION_PROBE_TIMEOUT'
        }
        elseif (-not $stdoutTask.Wait(500) -or -not $stderrTask.Wait(500)) {
            $result.status = 'VERSION_OUTPUT_TIMEOUT'
        }
        elseif ($process.ExitCode -ne 0) {
            $result.status = 'VERSION_PROBE_FAILED'
        }
        else {
            $text = $stdoutTask.Result + "`n" + $stderrTask.Result
            $match = [regex]::Match($text, $Pattern)
            if ($match.Success) {
                $result.verified = $true
                $result.version = $match.Groups[1].Value
                $result.status = 'VERSION_OBSERVED'
            }
            else { $result.status = 'VERSION_NOT_PARSED' }
        }
    }
    catch { $result.status = 'VERSION_PROBE_UNAVAILABLE' }
    finally { if ($null -ne $process) { $process.Dispose() } }
    # Raw command output and executable paths are deliberately excluded.
    [pscustomobject]$result
}

function Get-N95SoftwareVersion {
    param([string[]]$Paths, [string]$Arguments, [string]$Pattern)
    $result = [ordered]@{
        present = ($Paths.Count -gt 0)
        version_verified = $false
        version = $null
        status = 'NOT_FOUND_IN_SEARCHED_LOCATIONS'
    }
    foreach ($path in $Paths) {
        $probe = Invoke-N95VersionProbe -Executable $path -Arguments $Arguments -Pattern $Pattern
        $result.status = $probe.status
        if ($probe.verified) {
            $result.version_verified = $true
            $result.version = $probe.version
            break
        }
    }
    [pscustomobject]$result
}

function Get-N95FileVersion {
    param([string[]]$Paths)
    $result = [ordered]@{
        present = ($Paths.Count -gt 0)
        version_verified = $false
        version = $null
        version_source = 'LOCAL_FILE_VERSION_RESOURCE'
        status = 'NOT_FOUND_IN_SEARCHED_LOCATIONS'
    }
    foreach ($path in $Paths) {
        try {
            $metadata = [System.Diagnostics.FileVersionInfo]::GetVersionInfo($path)
            $match = [regex]::Match([string]$metadata.ProductVersion, '(\d+\.\d+\.\d+)')
            if ($match.Success) {
                $result.version_verified = $true
                $result.version = $match.Groups[1].Value
                $result.status = 'FILE_VERSION_OBSERVED_NOT_SERVER_VERSION'
                break
            }
            $result.status = 'VERSION_RESOURCE_UNAVAILABLE'
        }
        catch { $result.status = 'VERSION_RESOURCE_UNAVAILABLE' }
    }
    [pscustomobject]$result
}

function Get-N95LoopbackModels {
    $result = [ordered]@{
        attempted = $true
        endpoint = 'http://127.0.0.1:11434/api/tags'
        responding = $false
        model_count = $null
        status = 'UNKNOWN'
    }
    $response = $null
    $reader = $null
    try {
        $request = [System.Net.HttpWebRequest]::Create($result.endpoint)
        $request.Method = 'GET'
        $request.Proxy = $null
        $request.UseDefaultCredentials = $false
        $request.AllowAutoRedirect = $false
        $request.Timeout = 2500
        $request.ReadWriteTimeout = 2500
        $response = $request.GetResponse()
        if ([int]$response.StatusCode -ne 200) { throw 'NON_SUCCESS_RESPONSE' }
        $reader = [System.IO.StreamReader]::new($response.GetResponseStream())
        $buffer = New-Object char[] 4096
        $body = New-Object System.Text.StringBuilder
        $timer = [System.Diagnostics.Stopwatch]::StartNew()
        while (($read = $reader.Read($buffer, 0, $buffer.Length)) -gt 0) {
            if ($timer.ElapsedMilliseconds -gt 3000 -or $body.Length + $read -gt 262144) {
                throw 'RESPONSE_LIMIT_EXCEEDED'
            }
            [void]$body.Append($buffer, 0, $read)
        }
        $payload = $body.ToString() | ConvertFrom-Json
        if ($null -eq $payload -or $null -eq $payload.PSObject.Properties['models'] -or
            $payload.models -isnot [System.Array]) { throw 'INVALID_MODELS_RESPONSE' }
        $result.responding = $true
        $result.model_count = @($payload.models).Count
        $result.status = 'MODEL_LIST_OBSERVED_NO_INFERENCE_TEST'
    }
    catch { $result.status = 'LOOPBACK_UNAVAILABLE_OR_INVALID' }
    finally {
        if ($null -ne $reader) { $reader.Dispose() }
        if ($null -ne $response) { $response.Dispose() }
    }
    # Model names, prompts, and model metadata are not recorded.
    [pscustomobject]$result
}

function New-N95Check {
    param([string]$Id, [bool]$Required, [bool]$Passed, [string]$Meaning)
    [pscustomobject][ordered]@{
        id = $Id
        required = $Required
        pass = $Passed
        meaning = $Meaning
    }
}

$isNativeWindows = [Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT
if (-not $isNativeWindows) { throw 'This audit requires a local Windows session.' }

if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) { throw 'LOCALAPPDATA unavailable; specify a local OutputDirectory.' }
    $OutputDirectory = Join-Path $env:LOCALAPPDATA 'Network95\preflight'
}
# Local drive paths only. Avoid receipt writes to UNC paths or mapped network drives.
if ($OutputDirectory -notmatch '^[A-Za-z]:[\\/]') { throw 'OutputDirectory must be an absolute local drive path.' }
$outputPath = [System.IO.Path]::GetFullPath($OutputDirectory)
$outputDrive = [System.IO.DriveInfo]::new([System.IO.Path]::GetPathRoot($outputPath))
if ($outputDrive.DriveType -eq [System.IO.DriveType]::Network) { throw 'Network output drives are not allowed.' }
# Reject directory reparse points instead of following a junction to another location.
$outputAncestor = $outputPath
while (-not [string]::IsNullOrWhiteSpace($outputAncestor)) {
    if (Test-Path -LiteralPath $outputAncestor) {
        $outputItem = Get-Item -LiteralPath $outputAncestor -Force
        if (($outputItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'OutputDirectory must not traverse a directory reparse point.'
        }
    }
    $outputAncestor = [System.IO.Path]::GetDirectoryName($outputAncestor)
}

$hardware = [ordered]@{
    os_version = $null
    os_architecture = $null
    architecture_source = 'UNKNOWN'
    memory_bytes = $null
    system_disk_capacity_bytes = $null
    system_disk_free_bytes = $null
    memory_status = 'UNKNOWN'
    disk_status = 'UNKNOWN'
}
try {
    $runtimeArchitecture = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString().ToUpperInvariant()
    if ($runtimeArchitecture -in @('X64', 'X86', 'ARM64', 'ARM')) {
        $hardware.os_architecture = $runtimeArchitecture
        $hardware.architecture_source = 'RuntimeInformation.OSArchitecture'
    }
}
catch { }
try {
    $os = Get-CimInstance -ClassName Win32_OperatingSystem -Property Version, SystemDrive -OperationTimeoutSec 3
    $hardware.os_version = $os.Version
    if ($os.SystemDrive -match '^[A-Za-z]:$') {
        $disk = Get-CimInstance -ClassName Win32_LogicalDisk -Filter ("DeviceID='{0}'" -f $os.SystemDrive) -Property Size, FreeSpace -OperationTimeoutSec 3
        if ($null -ne $disk.Size -and $null -ne $disk.FreeSpace) {
            $hardware.system_disk_capacity_bytes = [long]$disk.Size
            $hardware.system_disk_free_bytes = [long]$disk.FreeSpace
            $hardware.disk_status = 'OBSERVED'
        }
    }
}
catch { }
try {
    $computer = Get-CimInstance -ClassName Win32_ComputerSystem -Property TotalPhysicalMemory -OperationTimeoutSec 3
    if ($null -ne $computer.TotalPhysicalMemory) {
        $hardware.memory_bytes = [long]$computer.TotalPhysicalMemory
        $hardware.memory_status = 'OBSERVED'
    }
}
catch { }
if ($null -eq $hardware.os_architecture) {
    try {
        $cpu = @(Get-CimInstance -ClassName Win32_Processor -Property Architecture, AddressWidth -OperationTimeoutSec 3)[0]
        $architectureMap = @{ 0 = 'X86'; 5 = 'ARM'; 6 = 'IA64'; 9 = 'X64'; 12 = 'ARM64' }
        if ($architectureMap.ContainsKey([int]$cpu.Architecture)) {
            $hardware.os_architecture = $architectureMap[[int]$cpu.Architecture]
            if ([int]$cpu.AddressWidth -eq 32 -and $hardware.os_architecture -eq 'X64') {
                $hardware.os_architecture = 'X86'
            }
            $hardware.architecture_source = 'CIM Win32_Processor Architecture/AddressWidth'
        }
    }
    catch { }
}

# Do not invoke py.exe: newer Python install managers can download a missing runtime.
$pythonPaths = @(Get-N95LocalApplication -Names @('python.exe', 'python3.exe'))
$python = [ordered]@{
    present = ($pythonPaths.Count -gt 0)
    version = $null
    version_verified = $false
    minimum_version = '3.11.0'
    minimum_satisfied = $false
    status = 'NOT_FOUND_IN_SEARCHED_LOCATIONS'
}
foreach ($pythonPath in $pythonPaths) {
    # Isolated mode, no site customization, and no bytecode writes.
    $pythonArguments = '-I -S -B -c "import sys; print(''N95_PYTHON_VERSION='' + ''.''.join(map(str, sys.version_info[:3])))"'
    $probe = Invoke-N95VersionProbe -Executable $pythonPath -Arguments $pythonArguments -Pattern 'N95_PYTHON_VERSION=(\d+\.\d+\.\d+)'
    if ($probe.verified) {
        $python.version_verified = $true
        $python.version = $probe.version
        $python.minimum_satisfied = [version]$probe.version -ge [version]'3.11.0'
        $python.status = 'VERSION_OBSERVED'
        if ($python.minimum_satisfied) { break }
    }
    elseif (-not $python.version_verified) { $python.status = $probe.status }
}

$tailscaleFallbacks = @()
if (-not [string]::IsNullOrWhiteSpace($env:ProgramFiles)) {
    $tailscaleFallbacks += Join-Path $env:ProgramFiles 'Tailscale\tailscale.exe'
}
if (-not [string]::IsNullOrWhiteSpace($env:ProgramW6432)) {
    $tailscaleFallbacks += Join-Path $env:ProgramW6432 'Tailscale\tailscale.exe'
}
$tailscalePaths = @(Get-N95LocalApplication -Names @('tailscale.exe') -Fallbacks $tailscaleFallbacks)
$tailscale = Get-N95SoftwareVersion -Paths $tailscalePaths -Arguments 'version' -Pattern '(?m)^\s*(\d+\.\d+\.\d+)'
$ollamaFallbacks = @()
if (-not [string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
    $ollamaFallbacks += Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'
}
$ollamaPaths = @(Get-N95LocalApplication -Names @('ollama.exe') -Fallbacks $ollamaFallbacks)
# Ollama --version can contact OLLAMA_HOST. Read file metadata without invoking it.
$ollama = Get-N95FileVersion -Paths $ollamaPaths
$ollamaLoopback = [pscustomobject][ordered]@{
    attempted = $false
    endpoint = 'http://127.0.0.1:11434/api/tags'
    responding = $false
    model_count = $null
    status = 'NOT_CHECKED_FOR_THIS_ROLE_OR_OLLAMA_NOT_FOUND'
}
if ($Role -eq 'RTX2080' -and $ollama.present) { $ollamaLoopback = Get-N95LoopbackModels }

$scriptHash = $null
try { $scriptHash = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant() }
catch { }
$expectedArchitecture = 'X64'
if ($Role -eq 'SURFACE') { $expectedArchitecture = 'ARM64' }
$isWorker = $Role -eq 'RTX2080'
$requiresPython = $Role -ne 'SURFACE'
$checks = @(
    (New-N95Check 'local_windows' $true $isNativeWindows 'Local Windows execution; this is not a remote-device audit.'),
    (New-N95Check 'role_architecture' $true ($hardware.os_architecture -eq $expectedArchitecture) ('Expected OS architecture: ' + $expectedArchitecture)),
    (New-N95Check 'python_3_11_or_newer' $requiresPython $python.minimum_satisfied 'Python command must run and report version >=3.11.0; optional on console.'),
    (New-N95Check 'tailscale_version' $true $tailscale.version_verified 'Installed CLI version only; tailnet login, connection, grants, and peers are not checked.'),
    (New-N95Check 'ollama_executable' $isWorker $ollama.present 'Local executable discovered; required only on inference worker.'),
    (New-N95Check 'ollama_file_version' $false $ollama.version_verified 'Optional file version metadata; not the running server version.'),
    (New-N95Check 'ollama_loopback' $isWorker $ollamaLoopback.responding 'Worker loopback model-list endpoint responded with a valid models array.'),
    (New-N95Check 'ollama_model_available' $isWorker ($ollamaLoopback.responding -and $ollamaLoopback.model_count -gt 0) 'At least one model listed; model execution, GPU acceleration, and quality are untested.'),
    (New-N95Check 'memory_observed' $false ($hardware.memory_status -eq 'OBSERVED') 'Reported capacity only; no workload capacity promise.'),
    (New-N95Check 'disk_observed' $false ($hardware.disk_status -eq 'OBSERVED') 'System drive capacity/free space only; no model storage sizing promise.'),
    (New-N95Check 'script_hash' $true ($null -ne $scriptHash) 'SHA-256 identifies this script; it is not a signature or independent attestation.')
)
$requiredChecks = @($checks | Where-Object { $_.required })
$failedRequired = @($requiredChecks | Where-Object { -not $_.pass })
$requiredPassed = $requiredChecks.Count - $failedRequired.Count
$receipt = [ordered]@{
    schema = 'network95.native-preflight.v1'
    receipt_id = [guid]::NewGuid().ToString()
    observed_at_utc = [DateTime]::UtcNow.ToString('o')
    status = 'AUDIT_ONLY_NOT_DEPLOYED'
    role_asserted = $Role
    role_authenticated = $false
    device_identity_collected = $false
    script_sha256 = $scriptHash
    hardware = $hardware
    software = [ordered]@{ python = $python; tailscale = $tailscale; ollama = $ollama }
    ollama_loopback = $ollamaLoopback
    checks = $checks
    summary = [ordered]@{
        required_checks = $requiredChecks.Count
        required_passed = $requiredPassed
        required_failed = $failedRequired.Count
        required_pass_percent = [math]::Round(100.0 * $requiredPassed / $requiredChecks.Count, 1)
        required_checks_pass = ($failedRequired.Count -eq 0)
        failed_required_ids = @($failedRequired | ForEach-Object { $_.id })
        meaning = 'Limited prerequisites only. Not deployment, connectivity, authentication, security certification, model execution, or autonomy readiness.'
    }
    collection_scope = @('OS architecture/version', 'memory capacity', 'system disk capacity/free space', 'selected application versions', 'RTX2080-only loopback model count', 'script SHA-256')
}

[void][System.IO.Directory]::CreateDirectory($outputPath)
$receiptName = 'preflight-{0}-{1}-{2}.json' -f $Role, [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'), $receipt.receipt_id
$receiptPath = Join-Path $outputPath $receiptName
$json = $receipt | ConvertTo-Json -Depth 9
$utf8 = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText($receiptPath, $json, $utf8)
Write-Output ('AUDIT_ONLY_NOT_DEPLOYED: {0}/{1} required checks passed.' -f $requiredPassed, $requiredChecks.Count)
Write-Output ('Local receipt: ' + $receiptName)
if ($failedRequired.Count -gt 0) { exit 2 }
exit 0
