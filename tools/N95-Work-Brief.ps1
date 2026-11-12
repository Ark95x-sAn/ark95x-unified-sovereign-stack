#requires -Version 5.1
<#
.SYNOPSIS
Runs the finite local folder-to-work-brief workflow with an existing Python.
.DESCRIPTION
No installation, launcher downloads, network requests, scheduled task, or service.
Use -CheckOnly to inspect prerequisites without creating a workflow output.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)] [string]$PythonExecutable,
    [Parameter(Mandatory = $true)] [string]$InputDirectory,
    [Parameter(Mandatory = $true)] [string]$OutputDirectory,
    [Parameter(Mandatory = $true)] [string]$AsOf,
    [switch]$CheckOnly
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

function Get-N95LocalPath {
    param([string]$Path)
    if ($Path -notmatch '^[A-Za-z]:[\\/]') { throw 'ABSOLUTE_LOCAL_DRIVE_PATH_REQUIRED' }
    $fullPath = [System.IO.Path]::GetFullPath($Path)
    $drive = [System.IO.DriveInfo]::new([System.IO.Path]::GetPathRoot($fullPath))
    if ($drive.DriveType -eq [System.IO.DriveType]::Network) { throw 'NETWORK_DRIVE_NOT_SUPPORTED' }
    $ancestor = $fullPath
    while (-not [string]::IsNullOrWhiteSpace($ancestor)) {
        if (Test-Path -LiteralPath $ancestor) {
            $item = Get-Item -LiteralPath $ancestor -Force
            if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw 'REPARSE_POINT_NOT_SUPPORTED'
            }
        }
        $ancestor = [System.IO.Path]::GetDirectoryName($ancestor)
    }
    $fullPath
}

function Test-N95Within {
    param([string]$Child, [string]$Parent)
    $prefix = $Parent.TrimEnd([char[]]@('\', '/')) + '\'
    ($Child.Equals($Parent, [StringComparison]::OrdinalIgnoreCase) -or
        $Child.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase))
}

function Get-N95PythonVersion {
    param([string]$Executable)
    $process = $null
    try {
        $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
        $startInfo.FileName = $Executable
        $startInfo.Arguments = '-I -S -B -c "import sys; print(''N95_VERSION='' + ''.''.join(map(str, sys.version_info[:3])))"'
        $startInfo.UseShellExecute = $false
        $startInfo.CreateNoWindow = $true
        $startInfo.RedirectStandardOutput = $true
        $startInfo.RedirectStandardError = $true
        $process = [System.Diagnostics.Process]::new()
        $process.StartInfo = $startInfo
        if (-not $process.Start()) { throw 'PYTHON_PROBE_NOT_STARTED' }
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit(3000)) {
            $process.Kill()
            throw 'PYTHON_PROBE_TIMEOUT'
        }
        if (-not $stdout.Wait(500) -or -not $stderr.Wait(500)) { throw 'PYTHON_PROBE_OUTPUT_TIMEOUT' }
        if ($process.ExitCode -ne 0) { throw 'PYTHON_PROBE_FAILED' }
        $match = [regex]::Match($stdout.Result, '(?m)^N95_VERSION=(\d+\.\d+\.\d+)\s*$')
        if (-not $match.Success) { throw 'PYTHON_VERSION_NOT_VERIFIED' }
        $match.Groups[1].Value
    }
    finally { if ($null -ne $process) { $process.Dispose() } }
}

$checks = [ordered]@{
    local_windows = ([Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT)
    local_python_executable = $false
    python_3_11_or_newer = $false
    workflow_module_present = $false
    supported_flat_input = $false
    output_separate_from_input = $false
    output_outside_git_checkout = $false
    valid_as_of_date = $false
}
$issues = [System.Collections.Generic.List[string]]::new()
$pythonVersion = $null
$pythonPath = $null
$inputPath = $null
$outputPath = $null
$checkoutRoot = $null
$fileCount = $null
$inputBytes = $null

try {
    if (-not $checks.local_windows) { throw 'LOCAL_WINDOWS_REQUIRED' }
    $checkoutRoot = Get-N95LocalPath -Path (Split-Path -Parent $PSScriptRoot)
    $moduleEntry = Join-Path $checkoutRoot 'n95_workflow\__main__.py'
    $checks.workflow_module_present = Test-Path -LiteralPath $moduleEntry -PathType Leaf
    if (-not $checks.workflow_module_present) { $issues.Add('WORKFLOW_MODULE_NOT_FOUND_IN_PORTABLE_PACKAGE') }

    $pythonPath = Get-N95LocalPath -Path $PythonExecutable
    if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf) -or
        [System.IO.Path]::GetFileName($pythonPath) -notmatch '^python(?:[0-9.]+)?\.exe$' -or
        $pythonPath -match '\\WindowsApps\\') { throw 'EXISTING_DIRECT_PYTHON_EXECUTABLE_REQUIRED' }
    $checks.local_python_executable = $true
    $pythonVersion = Get-N95PythonVersion -Executable $pythonPath
    $checks.python_3_11_or_newer = [version]$pythonVersion -ge [version]'3.11.0'
    if (-not $checks.python_3_11_or_newer) { $issues.Add('PYTHON_3_11_OR_NEWER_REQUIRED_NO_INSTALL_ATTEMPTED') }

    [void][DateTime]::ParseExact($AsOf, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
    $checks.valid_as_of_date = $true

    $inputPath = Get-N95LocalPath -Path $InputDirectory
    if (-not (Test-Path -LiteralPath $inputPath -PathType Container)) { throw 'INPUT_DIRECTORY_NOT_FOUND' }
    $inputEntries = @(Get-ChildItem -LiteralPath $inputPath -Force)
    $fileCount = $inputEntries.Count
    if ($fileCount -lt 1 -or $fileCount -gt 50) { throw 'INPUT_REQUIRES_1_TO_50_FILES' }
    $inputBytes = [long]0
    foreach ($entry in $inputEntries) {
        if ($entry.PSIsContainer -or
            ($entry.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
            $entry.Extension.ToLowerInvariant() -notin @('.txt', '.md')) {
            throw 'INPUT_MUST_CONTAIN_ONLY_FLAT_REGULAR_TXT_OR_MD_FILES'
        }
        $inputBytes += $entry.Length
    }
    if ($inputBytes -gt 1048576) { throw 'INPUT_LIMIT_1_MIB_EXCEEDED' }
    $checks.supported_flat_input = $true

    $outputPath = Get-N95LocalPath -Path $OutputDirectory
    if ((Test-Path -LiteralPath $outputPath) -and
        -not (Test-Path -LiteralPath $outputPath -PathType Container)) { throw 'OUTPUT_PATH_IS_NOT_A_DIRECTORY' }
    $checks.output_separate_from_input = -not ((Test-N95Within $outputPath $inputPath) -or (Test-N95Within $inputPath $outputPath))
    if (-not $checks.output_separate_from_input) { $issues.Add('INPUT_AND_OUTPUT_DIRECTORIES_MUST_NOT_OVERLAP') }
    $checks.output_outside_git_checkout = -not (Test-N95Within $outputPath $checkoutRoot)
    $ancestor = $outputPath
    while (-not [string]::IsNullOrWhiteSpace($ancestor)) {
        if (Test-Path -LiteralPath (Join-Path $ancestor '.git')) { $checks.output_outside_git_checkout = $false }
        $ancestor = [System.IO.Path]::GetDirectoryName($ancestor)
    }
    if (-not $checks.output_outside_git_checkout) { $issues.Add('OUTPUT_MUST_BE_OUTSIDE_PORTABLE_PACKAGE_AND_ALL_GIT_CHECKOUTS') }
}
catch {
    # Only known diagnostic codes are emitted; avoid exposing exception paths/content.
    $message = $_.Exception.Message
    if ($message -match '^[A-Z][A-Z0-9_]+$') { $issues.Add($message) }
    else { $issues.Add('PREFLIGHT_ITEM_UNAVAILABLE_OR_INVALID') }
}

$failedCheckNames = @($checks.Keys | Where-Object { -not $checks[$_] })
$preflight = [ordered]@{
    status = 'PREREQUISITES_CHECKED_NO_WORKFLOW_RUN'
    passed = ($failedCheckNames.Count -eq 0)
    checks = $checks
    failed_check_names = $failedCheckNames
    issues = @($issues.ToArray())
    python_version = $pythonVersion
    file_count = $fileCount
    input_bytes = $inputBytes
    as_of = $AsOf
    writes_performed_by_check = $false
    limitation = 'Checks paths, bounded file inventory and runtime version; does not prove content parsing, output permissions, completed delivery, or customer acceptance.'
}
if ($CheckOnly -or -not $preflight.passed) {
    $preflight | ConvertTo-Json -Depth 5
    if (-not $preflight.passed) { exit 2 }
    exit 0
}

# Site customization and PYTHON* settings are disabled. Input text is never code.
# The trusted package root supplies n95_workflow; nothing is installed into Python.
Push-Location -LiteralPath $checkoutRoot
try {
    & $pythonPath -E -S -B -m n95_workflow run --input $inputPath --output $outputPath --as-of $AsOf
    $workflowExitCode = $LASTEXITCODE
}
finally { Pop-Location }
exit $workflowExitCode
