# Native Windows prerequisite audit

This is a local audit entry point for a three-device setup: GM700 as the core, RTX2080 as the inference worker, and Surface Pro X as the ARM64 browser console. It writes one JSON receipt and does not install or deploy the system. The operator-supplied role is an assertion, not authenticated device identity.

The script targets Windows PowerShell 5.1 and requires no `pwsh` installation. It reads local CIM hardware data and selected installed application versions. It does not need an elevated terminal. Runtime execution and PowerShell parser validation have **not** been performed in the Linux build environment; review here was static only. A Windows run is the next required verification.

## Run locally on each device

The commands below assume this reviewed repository checkout is at `C:\Network95\network95-stack`. Substitute the actual local checkout path if different. Run the matching command in a normal Windows PowerShell terminal on each actual device.

GM700:

```powershell
powershell.exe -NoProfile -File "C:\Network95\network95-stack\tools\N95-Native-Preflight.ps1" -Role GM700
$LASTEXITCODE
```

RTX 2080 PC:

```powershell
powershell.exe -NoProfile -File "C:\Network95\network95-stack\tools\N95-Native-Preflight.ps1" -Role RTX2080
$LASTEXITCODE
```

Surface Pro X:

```powershell
powershell.exe -NoProfile -File "C:\Network95\network95-stack\tools\N95-Native-Preflight.ps1" -Role SURFACE
$LASTEXITCODE
```

Receipt files default to `$env:LOCALAPPDATA\Network95\preflight`. An explicit output directory must be an absolute local drive path, for example:

```powershell
powershell.exe -NoProfile -File "C:\Network95\network95-stack\tools\N95-Native-Preflight.ps1" -Role GM700 -OutputDirectory "C:\Network95\preflight"
```

The commands do not download code, change execution policy, or unblock files. If local policy prevents execution, preserve that result and review the local policy/source signature rather than bypassing it. The exact script can be inspected and hashed without running it:

```powershell
Get-Content -LiteralPath "C:\Network95\network95-stack\tools\N95-Native-Preflight.ps1"
Get-FileHash -LiteralPath "C:\Network95\network95-stack\tools\N95-Native-Preflight.ps1" -Algorithm SHA256
```

## Read the evidence

Exit `0` means the limited required prerequisite checks passed. Exit `2` means at least one required check failed or could not be verified. A terminating script/output error means no usable receipt should be assumed. Every successful receipt write has status `AUDIT_ONLY_NOT_DEPLOYED`, including a 100% prerequisite result.

| Check | GM700 | RTX2080 | Surface |
|---|---|---|---|
| Local Windows | Required | Required | Required |
| OS architecture | X64 required | X64 required | ARM64 required |
| Runnable Python >=3.11 | Required | Required | Observed, optional |
| Tailscale CLI version readable | Required | Required | Required |
| Ollama executable found | Observed, optional | Required | Observed, optional |
| Ollama file version metadata | Informational | Informational | Informational |
| Valid loopback `/api/tags` response | Not requested | Required when Ollama found | Not requested |
| At least one locally listed model | Not requested | Required | Not requested |
| Memory/disk capacities readable | Informational | Informational | Informational |
| Script SHA-256 available | Required | Required | Required |

Unknown hardware measurements are JSON `null` with `UNKNOWN` status. Application discovery searches application commands and limited standard install paths; `NOT_FOUND_IN_SEARCHED_LOCATIONS` is not proof that software exists nowhere on disk. Python is queried for its actual runtime version with isolated mode, site customization disabled, and bytecode writes disabled. Microsoft Store execution aliases and `py.exe` are skipped to avoid triggering runtime installation. No packages are installed. If Python is available only through a launcher, this limited audit may not discover it.

Tailscale collection runs `tailscale version`, not `status`, `up`, or peer scans. A readable CLI version does not establish login or connectivity. Ollama's version is read only from executable file metadata, because its version command can contact a configured server. If metadata is absent, the version remains unknown. Only the RTX2080 role with an Ollama executable found makes the request to `http://127.0.0.1:11434/api/tags`. That HTTP request disables proxies, credentials, and redirects, limits response size, and uses short timeouts. The model count is recorded without model names or inference requests. No Ollama command is executed.

The receipt excludes usernames, hostnames, executable paths, private IP addresses, peer lists, browser contents, wearable data, health records, secrets, and global environment dumps. Its hash identifies script contents; it does not authenticate the operator or prove the receipt has not been edited. Receipts remain on the machine where the script ran until separately transferred through an authorized route.

To view the latest local receipt's limited result:

```powershell
$receiptDirectory = Join-Path $env:LOCALAPPDATA 'Network95\preflight'
$latestReceipt = Get-ChildItem -LiteralPath $receiptDirectory -Filter 'preflight-*.json' | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
if ($null -ne $latestReceipt) {
    $receipt = Get-Content -LiteralPath $latestReceipt.FullName -Raw | ConvertFrom-Json
    $receipt.status
    $receipt.role_asserted
    $receipt.summary
    $receipt.checks | Format-Table id, required, pass -AutoSize
}
```

## Next verification boundary

Collect one real receipt per device before claiming all three are ready. The next deployment work must separately verify authenticated device registration, private connectivity, scoped task dispatch, storage restore, service startup/restart, and an actual approved model task with a result artifact. Neither a model listing nor the role name verifies that the RTX GPU is usable. This script performs none of those deployment actions.

Primary behavior references: [Microsoft CIM processor architecture values](https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-processor), [Get-FileHash for Windows PowerShell 5.1](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/get-filehash?view=powershell-5.1), and [Ollama model-list endpoint](https://docs.ollama.com/api/tags).
