#Requires -Version 5.1
<#
.SYNOPSIS
    Build PyInstaller output if needed, compile Inno Setup, refresh distribution README.

.DESCRIPTION
    From the repository root:
      .\packaging\windows\make_installer.ps1

    - Removes only prior installer outputs under Homogeneity_analyser_install
      (e.g. TimbralInstrumentalHomogeneitySetup.exe), never the repo root or unrelated files.
    - Runs build_windows.ps1 unless dist\TimbralInstrumentalHomogeneity\TimbralInstrumentalHomogeneity.exe
      already exists and -ForceBuild was not specified.
    - Runs Inno Setup ISCC.exe on TimbralInstrumentalHomogeneity.iss (output is written by Inno
      to Homogeneity_analyser_install\TimbralInstrumentalHomogeneitySetup.exe).
    - Copies packaging\windows\README_INSTALLATION.txt to
      Homogeneity_analyser_install\README_INSTALLATION.txt

.PARAMETER ForceBuild
    Always run build_windows.ps1 before compiling the installer.

.PARAMETER SkipPyInstaller
    Never run build_windows.ps1 (fail if dist\TimbralInstrumentalHomogeneity\TimbralInstrumentalHomogeneity.exe is missing).

.PARAMETER WhatIf
    Print steps only; do not remove files, build, or run ISCC.
#>
param(
    [switch] $ForceBuild,
    [switch] $SkipPyInstaller,
    [switch] $WhatIf
)

$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
$RepoRoot = Resolve-Path (Join-Path (Join-Path $here "..") "..")
$InstallRoot = Join-Path $RepoRoot "Homogeneity_analyser_install"
$DistDir = Join-Path $RepoRoot "dist\TimbralInstrumentalHomogeneity"
$DistExe = Join-Path $DistDir "TimbralInstrumentalHomogeneity.exe"
$Iss = Join-Path $RepoRoot "packaging\windows\TimbralInstrumentalHomogeneity.iss"
$ReadmeTemplate = Join-Path $here "README_INSTALLATION.txt"
$SetupExeName = "TimbralInstrumentalHomogeneitySetup.exe"
$SetupExePath = Join-Path $InstallRoot $SetupExeName

function Remove-InstallerOutputsOnly {
    if (-not (Test-Path $InstallRoot)) { return }
    $toRemove = @()
    $cand = Join-Path $InstallRoot $SetupExeName
    if (Test-Path $cand) { $toRemove += $cand }
    Get-ChildItem -LiteralPath $InstallRoot -Filter ($SetupExeName + ".*") -ErrorAction SilentlyContinue |
        Where-Object { -not $_.PSIsContainer } | ForEach-Object { $toRemove += $_.FullName }
    foreach ($p in ($toRemove | Select-Object -Unique)) {
        if ($WhatIf) {
            Write-Host "[WhatIf] Would remove: $p"
        } else {
            Remove-Item -LiteralPath $p -Force -ErrorAction Stop
            Write-Host "Removed previous installer output: $p"
        }
    }
}

function Copy-DistributionReadme {
    if (-not (Test-Path $ReadmeTemplate)) {
        throw "README template not found: $ReadmeTemplate"
    }
    if ($WhatIf) {
        Write-Host "[WhatIf] Would copy README to $(Join-Path $InstallRoot 'README_INSTALLATION.txt')"
        return
    }
    New-Item -ItemType Directory -Force $InstallRoot | Out-Null
    Copy-Item -LiteralPath $ReadmeTemplate -Destination (Join-Path $InstallRoot "README_INSTALLATION.txt") -Force
    Write-Host "Wrote: $(Join-Path $InstallRoot 'README_INSTALLATION.txt')"
}

$candidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
$iscc = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1

Write-Host "Repository root: $RepoRoot"
Write-Host "Install folder:  $InstallRoot"

if (-not $iscc) {
    throw "ISCC.exe not found. Install Inno Setup 6 from https://jrsoftware.org/isinfo.php"
}
if (-not (Test-Path $Iss)) {
    throw "Inno script not found: $Iss"
}

Remove-InstallerOutputsOnly

$runPyInstaller = $false
if ($SkipPyInstaller) {
    if (-not (Test-Path $DistExe)) {
        throw "PyInstaller output missing ($DistExe). Run without -SkipPyInstaller or run build_windows.ps1 first."
    }
    Write-Host "Skipping PyInstaller (-SkipPyInstaller)."
} elseif ($ForceBuild) {
    $runPyInstaller = $true
    Write-Host "ForceBuild: will run build_windows.ps1"
} elseif (-not (Test-Path $DistExe)) {
    $runPyInstaller = $true
    Write-Host "dist exe not found; will run build_windows.ps1"
} else {
    Write-Host "PyInstaller output present; skipping build_windows.ps1 (use -ForceBuild to rebuild)."
}

if ($runPyInstaller) {
    $bw = Join-Path $here "build_windows.ps1"
    if (-not (Test-Path $bw)) { throw "Missing: $bw" }
    if ($WhatIf) {
        Write-Host "[WhatIf] Would run: $bw"
    } else {
        Set-Location $RepoRoot
        & $bw
        if (-not (Test-Path $DistExe)) {
            throw "build_windows.ps1 finished but exe still missing: $DistExe"
        }
    }
}

if ($WhatIf) {
    Write-Host "[WhatIf] Would run: `"$iscc`" `"$Iss`""
    Copy-DistributionReadme
    Write-Host "[WhatIf] Done."
    exit 0
}

Set-Location $RepoRoot
& $iscc $Iss
if ($LASTEXITCODE -ne 0) {
    throw "ISCC failed with exit $LASTEXITCODE"
}

if (-not (Test-Path $SetupExePath)) {
    throw "Expected installer not found after ISCC: $SetupExePath"
}

Copy-DistributionReadme

$len = (Get-Item -LiteralPath $SetupExePath).Length
Write-Host ""
Write-Host "Installer created: $SetupExePath"
Write-Host "Installer size:    $len bytes ($([math]::Round($len / 1MB, 2)) MiB)"
Write-Host "SUCCESS"
