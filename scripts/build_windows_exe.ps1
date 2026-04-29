[CmdletBinding()]
param(
    [switch]$Clean,
    [string]$LogPath = "data/dynamic/tmp/pyinstaller_build.log"
)

$ErrorActionPreference = "Stop"

$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptPath "..")
$SpecPath = Join-Path $ProjectRoot "TextToSpeech.spec"
$DistPath = Join-Path $ProjectRoot "dist\TextToSpeech"
$ExePath = Join-Path $DistPath "TextToSpeech.exe"
$AzureSpeechDllPath = Join-Path $DistPath "_internal\azure\cognitiveservices\speech\Microsoft.CognitiveServices.Speech.core.dll"
$ResolvedLogPath = Join-Path $ProjectRoot $LogPath

Set-Location $ProjectRoot

if (-not (Get-Command poetry -ErrorAction SilentlyContinue)) {
    throw "Poetry is required to build the executable. Install Poetry, then run this script again."
}

if (-not (Test-Path $SpecPath)) {
    throw "Missing TextToSpeech.spec. Run this script from a complete repository checkout."
}

if ($Clean) {
    Write-Host "Removing previous build and dist folders..." -ForegroundColor Cyan
    foreach ($Path in @((Join-Path $ProjectRoot "build"), (Join-Path $ProjectRoot "dist"))) {
        if (Test-Path $Path) {
            Remove-Item -LiteralPath $Path -Recurse -Force
        }
    }
}

New-Item -ItemType Directory -Path (Split-Path -Parent $ResolvedLogPath) -Force | Out-Null

Write-Host "Checking PyInstaller availability..." -ForegroundColor Cyan
poetry run pyinstaller --version | Out-Null

$PyInstallerArgs = @(
    "run",
    "pyinstaller",
    "--noconfirm",
    "--log-level",
    "INFO"
)

if ($Clean) {
    $PyInstallerArgs += "--clean"
}

$PyInstallerArgs += $SpecPath

Write-Host "Starting PyInstaller. PyQt builds can take several minutes." -ForegroundColor Cyan
Write-Host "Build log: $ResolvedLogPath" -ForegroundColor Cyan
& poetry @PyInstallerArgs 2>&1 | Tee-Object -FilePath $ResolvedLogPath

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed. Review the build log at $ResolvedLogPath."
}

if (-not (Test-Path $ExePath)) {
    throw "Build finished, but $ExePath was not created."
}

if (-not (Test-Path $AzureSpeechDllPath)) {
    throw "Build finished, but the Azure Speech native DLL was not bundled at $AzureSpeechDllPath."
}

Write-Host ""
Write-Host "Executable created:" -ForegroundColor Green
Write-Host "  $ExePath"
Write-Host ""
Write-Host "Before sharing the build, verify provider settings and OCR requirements on a clean machine."
