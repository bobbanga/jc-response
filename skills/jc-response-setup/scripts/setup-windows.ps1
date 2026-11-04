param(
    [ValidateSet("inspect", "install", "refresh-docs", "configure")]
    [string]$Action = "inspect",
    [switch]$Confirm,
    [string]$PackagePath = ""
)

$ErrorActionPreference = "Stop"

function Get-SetupPin {
    $path = Join-Path (Split-Path -Parent $PSScriptRoot) "references\runtime-pin.json"
    Add-Type -AssemblyName System.Web.Extensions
    $serializer = New-Object System.Web.Script.Serialization.JavaScriptSerializer
    $serializer.MaxJsonLength = 67108864
    $serializer.RecursionLimit = 64
    $pin = $serializer.DeserializeObject([System.IO.File]::ReadAllText($path))
    $urlText = [string]$pin["download_url"]
    if ($urlText) {
        $url = [Uri]$urlText
        if ($url.Scheme -ne "https" -or $url.Host -ne "github.com") { throw "pin url rejected" }
    }
    if ([string]$pin["sha256"] -notmatch "^[0-9a-f]{64}$") { throw "pin hash rejected" }
    if ([int64]$pin["file_size"] -le 0) { throw "pin size rejected" }
    return $pin
}

function Test-ReparsePath([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $false }
    $item = Get-Item -LiteralPath $Path -Force
    return [bool]($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)
}

function Get-FileSha256([string]$Path) {
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

function Read-VersionFile([string]$Path) {
    $version = ""
    $contract = ""
    $csv = ""
    if (-not (Test-Path -LiteralPath $Path)) { return @{ version = ""; contract = ""; csv_schema = "" } }
    foreach ($line in [System.IO.File]::ReadAllLines($Path)) {
        if ($line.StartsWith("version=")) { $version = $line.Substring(8).Trim() }
        if ($line.StartsWith("schema=")) { $contract = $line.Substring(7).Trim() }
        if ($line.StartsWith("csv_schema=")) { $csv = $line.Substring(11).Trim() }
    }
    return @{ version = $version; contract = $contract; csv_schema = $csv }
}

function Test-SumsFile([string]$Root, [string]$SumsPath) {
    if (Test-ReparsePath $SumsPath) { return $false }
    foreach ($line in [System.IO.File]::ReadAllLines($SumsPath)) {
        if (-not $line.Trim()) { continue }
        $parts = $line -split "  ", 2
        if ($parts.Count -ne 2) { return $false }
        $relative = $parts[1].Trim().Replace("\", "/")
        if ($relative.StartsWith("*")) { $relative = $relative.Substring(1) }
        if ($relative.Contains("..") -or $relative.StartsWith("/") -or $relative.Contains(":")) { return $false }
        $target = Join-Path $Root ($relative.Replace("/", "\"))
        if (Test-ReparsePath $target) { return $false }
        if (-not (Test-Path -LiteralPath $target -PathType Leaf)) { return $false }
        if ((Get-FileSha256 $target) -ne $parts[0].ToLowerInvariant()) { return $false }
    }
    return $true
}

function Get-VersionRank([string]$Text) {
    $parts = @()
    foreach ($piece in ([string]$Text).Split(".")) {
        if (-not $piece) { return $null }
        $number = 0
        if (-not [int]::TryParse($piece, [ref]$number)) { return $null }
        $parts += $number
    }
    if ($parts.Count -eq 0) { return $null }
    return ,$parts
}

function Compare-VersionRank([string]$Left, [string]$Right) {
    $a = Get-VersionRank $Left
    $b = Get-VersionRank $Right
    if ($null -eq $a -or $null -eq $b) { return 0 }
    $count = [Math]::Max($a.Count, $b.Count)
    for ($i = 0; $i -lt $count; $i++) {
        $av = 0
        $bv = 0
        if ($i -lt $a.Count) { $av = [int]$a[$i] }
        if ($i -lt $b.Count) { $bv = [int]$b[$i] }
        if ($av -gt $bv) { return 1 }
        if ($av -lt $bv) { return -1 }
    }
    return 0
}

function Test-ReviewedPredecessor([string]$Root, $Info, $Pin) {
    $entries = $Pin["supported_upgrades"]
    if (-not $entries) { return $false }
    foreach ($entry in @($entries)) {
        if ([string]$entry["program_version"] -ne $Info.version) { continue }
        if ([string]$entry["contract"] -ne $Info.contract) { continue }
        $csv = [string]$entry["csv_schema"]
        if ($csv -and $Info.csv_schema -ne $csv) { continue }
        $hash = [string]$entry["exe_sha256"]
        $names = @($entry["exe_names"])
        if (-not $hash -or $names.Count -eq 0) { continue }
        $matched = $true
        foreach ($name in $names) {
            $exe = Join-Path $Root ("bin\" + [string]$name)
            if ((Test-ReparsePath $exe) -or -not (Test-Path -LiteralPath $exe -PathType Leaf) -or ((Get-FileSha256 $exe) -ne $hash)) {
                $matched = $false
                break
            }
        }
        if ($matched) { return $true }
    }
    return $false
}

function Get-ProgramClass([string]$Root, $Pin) {
    if (Test-ReparsePath $Root) { return "reparse" }
    if (-not (Test-Path -LiteralPath $Root)) { return "absent" }
    foreach ($db in @(Get-ChildItem -LiteralPath $Root -Filter *.db -Recurse -File -ErrorAction SilentlyContinue)) {
        return "mixed"
    }
    $info = Read-VersionFile (Join-Path $Root "VERSION")
    $expected = [string]$Pin["program_version"]
    if ($info.version -and $info.version -ne $expected) {
        if ((Compare-VersionRank $info.version $expected) -gt 0) { return "higher_version" }
        if (Test-ReviewedPredecessor $Root $info $Pin) { return "supported_upgrade" }
        return "unknown"
    }
    $exeHash = [string]$Pin["exe_sha256"]
    $exeOk = $true
    foreach ($name in @($Pin["exe_names"])) {
        $exe = Join-Path $Root ("bin\" + $name)
        if ((Test-ReparsePath $exe) -or -not (Test-Path -LiteralPath $exe -PathType Leaf) -or (Get-FileSha256 $exe) -ne $exeHash) {
            $exeOk = $false
        }
    }
    if (-not $exeOk) {
        if ($info.version -eq $expected) { return "different_binary" }
        return "unknown"
    }
    if ($info.contract -ne [string]$Pin["contract"]) { return "unknown" }
    $expectedCsv = [string]$Pin["csv_schema"]
    if ($expectedCsv -and $info.csv_schema -ne $expectedCsv) { return "unknown" }
    $sums = Join-Path $Root "SHA256SUMS.txt"
    if ((Test-Path -LiteralPath $sums -PathType Leaf) -and (Get-FileSha256 $sums) -eq [string]$Pin["sums_sha256"] -and (Test-SumsFile $Root $sums)) {
        return "match"
    }
    return "docs_or_incomplete"
}

function Test-ZipSafe([string]$ZipPath) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)
    $seen = @{}
    try {
        foreach ($entry in $zip.Entries) {
            $name = $entry.FullName.Replace("\", "/")
            if (-not $name -or $name.StartsWith("/") -or $name.StartsWith("../") -or $name.Contains("/../") -or $name.Contains(":")) {
                return $false
            }
            $mode = ($entry.ExternalAttributes -shr 16) -band 0xF000
            if ($mode -eq 0xA000) { return $false }
            $key = $name.ToLowerInvariant()
            if ($seen.ContainsKey($key)) { return $false }
            $seen[$key] = $true
        }
        return $true
    }
    finally { $zip.Dispose() }
}

function Expand-CheckedZip([string]$ZipPath, [string]$Destination) {
    if (-not (Test-ZipSafe $ZipPath)) { return $false }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($ZipPath, $Destination)
    foreach ($item in @(Get-ChildItem -LiteralPath $Destination -Recurse -Force)) {
        if (Test-ReparsePath $item.FullName) { return $false }
    }
    return $true
}

function Receive-FixedZip($Pin, [string]$Destination) {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $hosts = @($Pin["allowed_hosts"])
    $current = [Uri]$Pin["download_url"]
    for ($attempt = 1; $attempt -le 2; $attempt++) {
        if (Test-Path -LiteralPath $Destination) { Remove-Item -LiteralPath $Destination -Force }
        $hopUrl = $current
        $accepted = $false
        for ($hop = 0; $hop -le 5; $hop++) {
            if ($hopUrl.Scheme -ne "https" -or ($hosts -notcontains $hopUrl.Host)) { return "host_rejected" }
            $request = [System.Net.HttpWebRequest]::Create($hopUrl)
            $request.AllowAutoRedirect = $false
            $request.Timeout = 120000
            $request.ReadWriteTimeout = 120000
            $request.UserAgent = "JC-Response-setup/0.1.0"
            try { $response = $request.GetResponse() } catch { break }
            $status = [int]$response.StatusCode
            if ($status -ge 300 -and $status -lt 400) {
                $next = $response.Headers["Location"]
                $response.Close()
                if (-not $next) { return "redirect_rejected" }
                $hopUrl = if ($next.StartsWith("https://")) { [Uri]$next } else { New-Object System.Uri($hopUrl, $next) }
                continue
            }
            if ($status -ne 200) { $response.Close(); break }
            $stream = $response.GetResponseStream()
            $file = [System.IO.File]::Create($Destination)
            $buffer = New-Object byte[] 1048576
            $total = [int64]0
            $limit = [int64]$Pin["file_size"]
            try {
                while (($read = $stream.Read($buffer, 0, $buffer.Length)) -gt 0) {
                    $total += $read
                    if ($total -gt $limit) { return "size_rejected" }
                    $file.Write($buffer, 0, $read)
                }
            }
            finally { $file.Close(); $stream.Close(); $response.Close() }
            $accepted = $true
            break
        }
        if (-not $accepted) { continue }
        if ((Get-Item -LiteralPath $Destination).Length -ne [int64]$Pin["file_size"]) { Remove-Item -LiteralPath $Destination -Force; return "size_rejected" }
        if ((Get-FileSha256 $Destination) -ne [string]$Pin["sha256"]) { Remove-Item -LiteralPath $Destination -Force; return "hash_rejected" }
        return "ok"
    }
    return "download_failed"
}

function Test-ReleaseExes([string]$Root, $Pin) {
    foreach ($name in @($Pin["exe_names"])) {
        $path = Join-Path $Root ("bin\" + $name)
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { return $false }
        if ((Get-FileSha256 $path) -ne [string]$Pin["exe_sha256"]) { return $false }
    }
    return $true
}

function Resolve-InstallResult([int]$ExitCode, [string]$Status, [string]$Extract, [string]$Program, $Pin) {
    $accepted = @($Pin["accepted_install_status"])
    if ($ExitCode -ne 0 -or ($accepted -notcontains $Status)) { return "rejected" }
    if ($Extract -and -not (Test-BinTreesEqual (Join-Path $Extract "bin") (Join-Path $Program "bin"))) { return "bin_mismatch" }
    $info = Read-VersionFile (Join-Path $Program "VERSION")
    if ($info.version -ne [string]$Pin["program_version"] -or $info.contract -ne [string]$Pin["contract"]) { return "version_mismatch" }
    if (-not (Test-ReleaseExes $Program $Pin)) { return "exe_mismatch" }
    return "verified"
}

function Test-BinTreesEqual([string]$Left, [string]$Right) {
    if (-not (Test-Path -LiteralPath $Left) -or -not (Test-Path -LiteralPath $Right)) { return $false }
    $map = @{}
    foreach ($file in @(Get-ChildItem -LiteralPath $Left -Recurse -File)) {
        $name = $file.FullName.Substring($Left.Length).TrimStart("\").Replace("\", "/").ToLowerInvariant()
        $map[$name] = Get-FileSha256 $file.FullName
    }
    $rightCount = 0
    foreach ($file in @(Get-ChildItem -LiteralPath $Right -Recurse -File)) {
        $rightCount += 1
        $name = $file.FullName.Substring($Right.Length).TrimStart("\").Replace("\", "/").ToLowerInvariant()
        if (-not $map.ContainsKey($name) -or $map[$name] -ne (Get-FileSha256 $file.FullName)) { return $false }
    }
    return $map.Count -eq $rightCount
}

function Update-DocWhitelist([string]$Extract, [string]$Program, $Pin) {
    if (-not (Test-BinTreesEqual (Join-Path $Extract "bin") (Join-Path $Program "bin"))) { return "bins_differ" }
    $backups = @()
    foreach ($relative in @($Pin["doc_files"])) {
        $source = Join-Path $Extract ($relative.Replace("/", "\"))
        $target = Join-Path $Program ($relative.Replace("/", "\"))
        if (Test-ReparsePath $source -or (Test-ReparsePath $target) -or (Test-ReparsePath (Split-Path -Parent $target))) { return "reparse" }
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { return "source_missing" }
        $parent = Split-Path -Parent $target
        if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent | Out-Null }
        $backup = $target + ".setup-bak"
        if (Test-Path -LiteralPath $target -PathType Leaf) {
            try { [System.IO.File]::Copy($target, $backup, $true) } catch { return "docs_locked" }
            $backups += ,@($target, $backup)
        }
        $temp = $target + ".setup-tmp"
        try {
            [System.IO.File]::Copy($source, $temp, $true)
            if (Test-Path -LiteralPath $target) { [System.IO.File]::Replace($temp, $target, [NullString]::Value) }
            else { [System.IO.File]::Move($temp, $target) }
        }
        catch {
            foreach ($pair in $backups) {
                if (Test-Path -LiteralPath $pair[1]) { try { [System.IO.File]::Copy($pair[1], $pair[0], $true) } catch { } }
            }
            return "docs_locked"
        }
    }
    foreach ($relative in @($Pin["doc_files"])) {
        $source = Join-Path $Extract ($relative.Replace("/", "\"))
        $target = Join-Path $Program ($relative.Replace("/", "\"))
        if ((Get-FileSha256 $source) -ne (Get-FileSha256 $target)) { return "docs_mismatch" }
    }
    return "docs_refreshed"
}

function Read-JsonFile([string]$Path) {
    Add-Type -AssemblyName System.Web.Extensions
    $serializer = New-Object System.Web.Script.Serialization.JavaScriptSerializer
    $serializer.MaxJsonLength = 67108864
    $serializer.RecursionLimit = 256
    $text = [System.IO.File]::ReadAllText($Path)
    return @{ text = $text; data = $serializer.DeserializeObject($text); serializer = $serializer }
}

function Get-ConfigPlan([string]$Path, [string]$Official) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return "add" }
    try { $doc = Read-JsonFile $Path } catch { return "invalid" }
    if ($null -eq $doc.data -or -not ($doc.data -is [System.Collections.IDictionary])) { return "invalid" }
    $servers = $doc.data["mcpServers"]
    if ($null -eq $servers) { return "add" }
    if (-not ($servers -is [System.Collections.IDictionary])) { return "invalid" }
    if (-not $servers.ContainsKey("jc-response")) { return "add" }
    $entry = $servers["jc-response"]
    if (-not ($entry -is [System.Collections.IDictionary])) { return "conflict" }
    $type = [string]$entry["type"]
    $command = ([string]$entry["command"]).Replace("/", "\").Trim()
    $officialText = $Official.Replace("/", "\").Trim()
    $args = $entry["args"]
    $argsOk = $null -eq $args -or ($args -is [System.Collections.IList] -and $args.Count -eq 0)
    if (($type -eq "" -or $type -eq "stdio") -and $command.Equals($officialText, [System.StringComparison]::OrdinalIgnoreCase) -and $argsOk) {
        return "reuse"
    }
    return "conflict"
}

function Get-OtherConfig([string]$Path) {
    $root = Split-Path -Parent (Split-Path -Parent $Path)
    $candidates = @(
        (Join-Path $root ".codebuddy\mcp.json"),
        (Join-Path $env:LOCALAPPDATA "WorkBuddy\mcp.json"),
        (Join-Path $env:APPDATA "WorkBuddy\mcp.json")
    )
    foreach ($candidate in $candidates) {
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { continue }
        try {
            $doc = Read-JsonFile $candidate
            $servers = $doc.data["mcpServers"]
            if ($servers -is [System.Collections.IDictionary] -and $servers.ContainsKey("jc-response")) { return $candidate }
        }
        catch { return "unreadable" }
    }
    return ""
}

function Invoke-Product([string]$Exe, [string]$Arguments) {
    $info = New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName = $Exe
    $info.Arguments = $Arguments
    $info.WorkingDirectory = Split-Path -Parent $Exe
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $info
    [void]$process.Start()
    $outTask = $process.StandardOutput.ReadToEndAsync()
    $errTask = $process.StandardError.ReadToEndAsync()
    if (-not $process.WaitForExit(240000)) {
        try { $process.Kill() } catch { }
        return @{ exit = 1; status = "timeout"; text = "" }
    }
    $process.WaitForExit()
    [void]$outTask.Wait(10000)
    [void]$errTask.Wait(10000)
    $text = $outTask.Result
    $status = "unreadable"
    if ($text.Trim()) {
        try {
            Add-Type -AssemblyName System.Web.Extensions
            $serializer = New-Object System.Web.Script.Serialization.JavaScriptSerializer
            $payload = $serializer.DeserializeObject($text)
            if ($payload -is [System.Collections.IDictionary] -and $payload.ContainsKey("status")) {
                $status = [string]$payload["status"]
            }
        }
        catch { $status = "unreadable" }
    }
    return @{ exit = [int]$process.ExitCode; status = $status; text = $text }
}

function Invoke-Setup {
    if ($env:OS -ne "Windows_NT") { Write-Output "platform=unsupported"; return 3 }
    $pin = Get-SetupPin
    $program = Join-Path $env:LOCALAPPDATA "Programs\JC_response"
    $data = Join-Path $env:LOCALAPPDATA "JC_response"
    $config = Join-Path $env:USERPROFILE ".workbuddy\mcp.json"
    $official = Join-Path $program "bin\jctrans-mcp.exe"
    $class = Get-ProgramClass $program $pin
    Write-Output ("class=" + $class)
    Write-Output ("signed=" + [string]$pin["signed"])
    Write-Output ("bytes=" + [string]$pin["file_size"])
    Write-Output ("source=" + [string]$pin["download_url"])
    $oldSkill = Join-Path $env:USERPROFILE ".workbuddy\skills\jctrans-response-assistant\SKILL.md"
    if (Test-Path -LiteralPath $oldSkill -PathType Leaf) {
        $oldText = [System.IO.File]::ReadAllText($oldSkill)
        if ($oldText.Contains("inquiry-response assistant")) { Write-Output "old_skill=dev_command" }
        else { Write-Output "old_skill=present" }
    }
    else { Write-Output "old_skill=absent" }
    if ($Action -eq "inspect") { Write-Output "downloaded=0"; Write-Output "changed=0"; return 0 }
    if (-not $Confirm) { Write-Output "consent=required"; Write-Output "downloaded=0"; return 2 }
    if ($Action -eq "configure") {
        $other = Get-OtherConfig $config
        if ($other) { Write-Output "config=duplicate"; return 5 }
        $plan = Get-ConfigPlan $config $official
        Write-Output ("config=" + $plan)
        if ($plan -eq "reuse") { return 0 }
        if ($plan -ne "add") { return 5 }
        if (-not (Test-Path -LiteralPath $official -PathType Leaf)) { Write-Output "config=install_required"; return 4 }
        $before = ""
        if (Test-Path -LiteralPath $config) { $before = [System.IO.File]::ReadAllText($config) }
        $result = Invoke-Product (Join-Path $program "bin\JC_response.exe") "--configure-workbuddy --json"
        Write-Output ("configure_status=" + $result.status)
        Write-Output ("configure_exit=" + $result.exit)
        $accepted = @($pin["accepted_configure_status"])
        if ($result.exit -ne 0 -or ($accepted -notcontains $result.status)) { return 5 }
        if ($before -and (Test-Path -LiteralPath $config)) {
            $after = Read-JsonFile $config
            $prior = Read-JsonText $before
            foreach ($name in @($prior.data["mcpServers"].Keys)) {
                if ($name -eq "jc-response") { continue }
                $left = $prior.serializer.Serialize($prior.data["mcpServers"][$name])
                $right = $after.serializer.Serialize($after.data["mcpServers"][$name])
                if ($left -ne $right) { Write-Output "config=other_changed"; return 5 }
            }
        }
        return 0
    }
    if ($class -eq "match") { Write-Output "downloaded=0"; Write-Output "install=reused"; return 0 }
    if ($class -eq "higher_version" -or $class -eq "unknown" -or $class -eq "reparse" -or $class -eq "mixed") {
        Write-Output "install=stopped"; Write-Output "downloaded=0"; return 4
    }
    if (-not [string]$pin["download_url"] -and -not $PackagePath) { Write-Output "download=unpublished"; Write-Output "downloaded=0"; return 3 }
    $temp = Join-Path $env:TEMP ("jc-response-setup-" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $temp | Out-Null
    try {
        $zip = Join-Path $temp "package.zip"
        if ($PackagePath) {
            if ((Test-ReparsePath $PackagePath) -or -not (Test-Path -LiteralPath $PackagePath -PathType Leaf)) { Write-Output "download=local_rejected"; Write-Output "downloaded=0"; return 3 }
            if ((Get-Item -LiteralPath $PackagePath).Length -ne [int64]$pin["file_size"] -or (Get-FileSha256 $PackagePath) -ne [string]$pin["sha256"]) {
                Write-Output "download=local_rejected"; Write-Output "downloaded=0"; return 3
            }
            Copy-Item -LiteralPath $PackagePath -Destination $zip -Force
            Write-Output "download=pinned-local"
            Write-Output "downloaded=0"
        }
        elseif (-not [string]$pin["download_url"]) { Write-Output "download=unpublished"; Write-Output "downloaded=0"; return 3 }
        else {
            $received = Receive-FixedZip $pin $zip
            Write-Output ("download=" + $received)
            if ($received -ne "ok") { Write-Output "downloaded=0"; return 3 }
            Write-Output "downloaded=1"
        }
        $extract = Join-Path $temp "extract"
        if (-not (Expand-CheckedZip $zip $extract)) { Write-Output "zip=rejected"; return 3 }
        if (-not (Test-ReleaseExes $extract $pin)) { Write-Output "release_exe_mismatch"; return 3 }
        $binsEqual = Test-BinTreesEqual (Join-Path $extract "bin") (Join-Path $program "bin")
        if ($Action -eq "refresh-docs") {
            if (-not $binsEqual) { Write-Output "docs=bins_differ"; return 4 }
            $refreshed = Update-DocWhitelist $extract $program $pin
            Write-Output ("docs=" + $refreshed)
            if ($refreshed -ne "docs_refreshed") { return 4 }
            return 0
        }
        if ($binsEqual) { Write-Output "install=not_run"; Write-Output "next=refresh-docs"; return 0 }
        $installer = Join-Path $extract "bin\JC_response.exe"
        $result = Invoke-Product $installer "--install-user --json"
        $judged = Resolve-InstallResult $result.exit $result.status $extract $program $pin
        Write-Output ("install_status=" + $result.status)
        Write-Output ("install_exit=" + $result.exit)
        Write-Output ("install_judged=" + $judged)
        if ($judged -ne "verified") { return 4 }
        return 0
    }
    finally {
        if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue }
    }
}

function Read-JsonText([string]$Text) {
    Add-Type -AssemblyName System.Web.Extensions
    $serializer = New-Object System.Web.Script.Serialization.JavaScriptSerializer
    $serializer.MaxJsonLength = 67108864
    $serializer.RecursionLimit = 256
    return @{ text = $Text; data = $serializer.DeserializeObject($Text); serializer = $serializer }
}

if ($MyInvocation.InvocationName -ne ".") {
    $result = @(Invoke-Setup)
    $code = 1
    foreach ($item in $result) {
        if ($item -is [int]) { $code = $item }
        else { Write-Output $item }
    }
    exit $code
}
