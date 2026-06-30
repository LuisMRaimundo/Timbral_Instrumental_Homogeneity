#Requires -Version 5.1
<#
.SYNOPSIS
    Compile the Inno Setup installer script (draft).

.DESCRIPTION
    Requires Inno Setup 6 (ISCC.exe). Default install path:
      ${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe

    Run after build_pyinstaller.ps1 -Run so dist\TimbralInstrumentalHomogeneity exists.

    Inno writes TimbralInstrumentalHomogeneitySetup.exe to Homogeneity_analyser_install\ (see .iss).

.PARAMETER Run
    If set, runs ISCC. Otherwise prints the command only.
#>
param([switch] $Run)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path (Join-Path $PSScriptRoot "..") "..")
$InstallRoot = Join-Path $RepoRoot "Homogeneity_analyser_install"
$Iss = Join-Path $RepoRoot "packaging\windows\TimbralInstrumentalHomogeneity.iss"

$candidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
$iscc = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $iscc) {
    Write-Warning "ISCC.exe not found. Install Inno Setup 6 from https://jrsoftware.org/isinfo.php"
    if ($Run) { throw "ISCC required when -Run is set." }
    exit 0
}

$dist = Join-Path $RepoRoot "dist\TimbralInstrumentalHomogeneity"
if (-not (Test-Path $dist)) {
    Write-Warning "PyInstaller output not found: $dist`nRun packaging\windows\build_pyinstaller.ps1 -Run first."
}

$args = @($Iss)
Write-Host "Would run: `"$iscc`" $($args -join ' ')"

if (-not $Run) {
    Write-Host "Dry run. Pass -Run to compile the installer."
    exit 0
}

New-Item -ItemType Directory -Force $InstallRoot | Out-Null

& $iscc @args
if ($LASTEXITCODE -ne 0) { throw "ISCC failed with exit $LASTEXITCODE" }

$setupExe = Join-Path $InstallRoot "TimbralInstrumentalHomogeneitySetup.exe"
if (-not (Test-Path $setupExe)) {
    throw "Expected installer not found: $setupExe"
}
Write-Host "Installer: $setupExe"
