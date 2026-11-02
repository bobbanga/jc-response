param(
    [string]$ConfigPath = "",
    [switch]$Confirm,
    [string]$Restore,
    [switch]$AllowLive
)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Web.Extensions

function Normalize-PathText([string]$PathText) {
    if (-not $PathText) { return "" }
    return [System.IO.Path]::GetFullPath($PathText).TrimEnd("\").ToLowerInvariant()
}

function New-MarketSerializer {
    $serializer = New-Object System.Web.Script.Serialization.JavaScriptSerializer
    $serializer.MaxJsonLength = 67108864
    $serializer.RecursionLimit = 256
    return $serializer
}

function Read-MarketDocument([string]$Path) {
    $serializer = New-MarketSerializer
    $text = [System.IO.File]::ReadAllText($Path)
    return @{ text = $text; data = $serializer.DeserializeObject($text); serializer = $serializer }
}

function Test-MarketKey($Map, [string]$Name) {
    if ($null -eq $Map) { return $false }
    foreach ($key in @($Map.Keys)) { if ([string]$key -eq $Name) { return $true } }
    return $false
}

function Get-MarketField($Entry, [string]$Name) {
    if (-not (Test-MarketKey $Entry $Name)) { return $null }
    return $Entry[$Name]
}

function Get-OfficialMcpPath {
    $local = [Environment]::GetEnvironmentVariable("LOCALAPPDATA")
    if (-not $local) { return $null }
    return Join-Path $local "Programs\JC_response\bin\jctrans-mcp.exe"
}

function Get-EntryKind($Entry) {
    if ($null -eq $Entry) { return "absent" }
    $type = [string](Get-MarketField $Entry "type")
    if ($type -and $type -ne "stdio") { return "unknown_source" }
    $official = Get-OfficialMcpPath
    if (-not $official -or -not (Test-Path -LiteralPath $official -PathType Leaf)) { return "unverified" }
    $command = ([string](Get-MarketField $Entry "command")).Replace("/", "\")
    if ((Normalize-PathText $command) -ne (Normalize-PathText $official)) {
        return "unknown_source"
    }
    $args = Get-MarketField $Entry "args"
    if ($null -ne $args) {
        $count = 0
        foreach ($unused in $args) { $count++ }
        if ($count -ne 0) { return "unknown_source" }
    }
    return "official"
}

function Write-MarketConfigIfUnchanged([string]$Path, [string]$OriginalText, [string]$NewText) {
    $encoding = New-Object System.Text.UTF8Encoding $false
    $temp = $Path + ".migrate-tmp"
    [System.IO.File]::WriteAllText($temp, $NewText, $encoding)
    $current = [System.IO.File]::ReadAllText($Path)
    if ($current -ne $OriginalText) {
        Remove-Item -LiteralPath $temp -Force
        return "concurrent"
    }
    [System.IO.File]::Replace($temp, $Path, [NullString]::Value)
    return "ok"
}

function Invoke-Migration {
    if (-not $ConfigPath) { Write-Output "config missing"; return 2 }
    $live = Join-Path $env:USERPROFILE ".workbuddy\mcp.json"
    if (-not $AllowLive -and (Normalize-PathText $ConfigPath) -eq (Normalize-PathText $live)) {
        Write-Output "refusing the live WorkBuddy config"
        return 2
    }
    if (-not (Test-Path -LiteralPath $ConfigPath -PathType Leaf)) {
        Write-Output "config missing"
        return 2
    }
    $current = Read-MarketDocument $ConfigPath
    if ($null -eq $current.data -or -not (Test-MarketKey $current.data "mcpServers")) {
        Write-Output "mcpServers missing"
        return 2
    }
    $servers = $current.data["mcpServers"]
    if ($Restore) {
        if (-not $Confirm) { Write-Output "restore requires -Confirm"; return 2 }
        $configDir = Split-Path -Parent (Normalize-PathText $ConfigPath)
        $restoreDir = Split-Path -Parent (Normalize-PathText $Restore)
        $restoreName = Split-Path -Leaf $Restore
        if ($configDir -ne $restoreDir -or $restoreName -notlike "*.bak-*") {
            Write-Output "restore file must be a sibling backup"
            return 2
        }
        $backup = Read-MarketDocument $Restore
        $backupServers = $backup.data["mcpServers"]
        $backupEntry = $null
        if (Test-MarketKey $backupServers "jc-response") { $backupEntry = $backupServers["jc-response"] }
        $kind = Get-EntryKind $backupEntry
        if ($kind -ne "official") { Write-Output "migrate=$kind"; return 3 }
        $backupJson = $current.serializer.Serialize($backupEntry)
        if (Test-MarketKey $servers "jc-response") {
            $currentJson = $current.serializer.Serialize($servers["jc-response"])
            if ($currentJson -ne $backupJson) { Write-Output "conflict=target"; return 4 }
            Write-Output "restored=unchanged"
            return 0
        }
        $servers["jc-response"] = $backupEntry
        $written = Write-MarketConfigIfUnchanged $ConfigPath $current.text $current.serializer.Serialize($current.data)
        if ($written -eq "concurrent") { Write-Output "conflict=concurrent"; return 5 }
        Write-Output "restored=target"
        return 0
    }
    $entry = $null
    if (Test-MarketKey $servers "jc-response") { $entry = $servers["jc-response"] }
    $kind = Get-EntryKind $entry
    if ($kind -eq "absent") { Write-Output "remove=no"; return 0 }
    if ($kind -ne "official") { Write-Output "migrate=$kind"; return 3 }
    $others = @()
    foreach ($name in @($servers.Keys)) { if ($name -ne "jc-response") { $others += $name } }
    Write-Output ("others=" + ($others -join ","))
    if (-not $Confirm) { Write-Output "remove=planned"; return 0 }
    $stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
    Copy-Item -LiteralPath $ConfigPath -Destination "$ConfigPath.bak-$stamp" -Force
    $servers.Remove("jc-response")
    $fresh = Read-MarketDocument $ConfigPath
    if ($fresh.text -ne $current.text) { Write-Output "conflict=concurrent"; return 5 }
    $written = Write-MarketConfigIfUnchanged $ConfigPath $current.text $current.serializer.Serialize($current.data)
    if ($written -eq "concurrent") { Write-Output "conflict=concurrent"; return 5 }
    Write-Output "remove=done"
    Write-Output "backup=1"
    return 0
}

if ($MyInvocation.InvocationName -ne ".") {
    $result = @(Invoke-Migration)
    $code = 1
    foreach ($item in $result) {
        if ($item -is [int]) { $code = $item }
        else { Write-Output $item }
    }
    exit $code
}
