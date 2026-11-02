param(
    [Parameter(Mandatory = $true)][string]$ConfigPath,
    [switch]$Confirm,
    [string]$Restore,
    [switch]$AllowLive
)
$ErrorActionPreference = "Stop"

function Normalize-PathText([string]$PathText) {
    return [System.IO.Path]::GetFullPath($PathText).TrimEnd("\").ToLowerInvariant()
}

$live = Join-Path $env:USERPROFILE ".workbuddy\mcp.json"
if (-not $AllowLive -and (Normalize-PathText $ConfigPath) -eq (Normalize-PathText $live)) {
    Write-Error "refusing the live WorkBuddy config"
    exit 2
}
if (-not (Test-Path -LiteralPath $ConfigPath -PathType Leaf)) {
    Write-Error "config missing"
    exit 2
}
if ($Restore) {
    if (-not $Confirm) { Write-Error "restore requires -Confirm"; exit 2 }
    $configDir = Split-Path -Parent (Normalize-PathText $ConfigPath)
    $restoreDir = Split-Path -Parent (Normalize-PathText $Restore)
    $restoreName = Split-Path -Leaf $Restore
    if ($configDir -ne $restoreDir -or $restoreName -notlike "*.bak-*") {
        Write-Error "restore file must be a sibling backup"
        exit 2
    }
    Copy-Item -LiteralPath $Restore -Destination $ConfigPath -Force
    Write-Output "restored=1"
    exit 0
}

$data = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $data.mcpServers) { Write-Error "mcpServers missing"; exit 2 }
$entry = $data.mcpServers.PSObject.Properties["jc-response"]
$remove = $false
if ($null -ne $entry) {
    $command = ([string]$entry.Value.command).Replace("/", "\")
    if ($command.ToLowerInvariant().EndsWith("\jctrans-mcp.exe")) { $remove = $true }
    else { Write-Output "remove=blocked"; exit 3 }
}
$others = @($data.mcpServers.PSObject.Properties.Name | Where-Object { $_ -ne "jc-response" })
Write-Output ("others=" + ($others -join ","))
if (-not $remove) { Write-Output "remove=no"; exit 0 }
if (-not $Confirm) { Write-Output "remove=planned"; exit 0 }
$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$backup = "$ConfigPath.bak-$stamp"
Copy-Item -LiteralPath $ConfigPath -Destination $backup -Force
$data.mcpServers.PSObject.Properties.Remove("jc-response")
$json = $data | ConvertTo-Json -Depth 8
[System.IO.File]::WriteAllText(((Resolve-Path -LiteralPath $ConfigPath).Path), $json)
Write-Output "remove=done"
Write-Output "backup=1"
exit 0
