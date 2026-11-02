param(
    [Parameter(Mandatory = $true)][string]$OutputZip
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$stage = Join-Path ([System.IO.Path]::GetTempPath()) ("jc-response-market-stage-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $stage | Out-Null
try {
    $csc = "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
    $exe = Join-Path $stage "jc-response-launch.exe"
    & $csc /nologo /optimize+ /target:exe "/out:$exe" `
        /r:System.IO.Compression.dll /r:System.IO.Compression.FileSystem.dll /r:System.Web.Extensions.dll `
        (Join-Path $root "connector\launch\Program.cs")
    if ($LASTEXITCODE -ne 0) { throw "compiler failed" }
    foreach ($name in @("connector-meta.json", "mcp.json", "plugin.json", "runtime-pin.json", "icon.svg")) {
        Copy-Item -LiteralPath (Join-Path $root "connector\$name") -Destination (Join-Path $stage $name)
    }
    $skillSource = Join-Path $root "skills\jc-response-preview\SKILL.md"
    $skillTarget = Join-Path $stage "skills\jc-response-preview"
    New-Item -ItemType Directory -Path $skillTarget | Out-Null
    Copy-Item -LiteralPath $skillSource -Destination (Join-Path $skillTarget "SKILL.md")
    Copy-Item -LiteralPath (Join-Path $root "scripts\migrate_workbuddy_custom.ps1") -Destination (Join-Path $stage "migrate-custom.ps1")
    $sourceHash = (Get-FileHash -Algorithm SHA256 $skillSource).Hash
    $copyHash = (Get-FileHash -Algorithm SHA256 (Join-Path $skillTarget "SKILL.md")).Hash
    if ($sourceHash -ne $copyHash) { throw "skill copy mismatch" }
    $outputDir = Split-Path -Parent $OutputZip
    if ($outputDir) { New-Item -ItemType Directory -Force -Path $outputDir | Out-Null }
    if (Test-Path -LiteralPath $OutputZip) { Remove-Item -LiteralPath $OutputZip -Force }
    Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $OutputZip
    $length = (Get-Item -LiteralPath $OutputZip).Length
    if ($length -ge 20000000) { throw "market zip is too large" }
    Write-Output ("bytes=" + $length)
}
finally {
    Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
}
