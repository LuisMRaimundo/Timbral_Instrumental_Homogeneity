#Requires -Version 5.1
<#
.SYNOPSIS
    Build the onedir PyInstaller bundle (Timbral Instrumental Homogeneity).

.DESCRIPTION
    Run from the repository root with a dev venv that has the project + pyinstaller installed:
      pip install -e ".[dev]"
      pip install pyinstaller

    Does not run PyInstaller unless -Run is passed (default is dry-run / checks only).

.PARAMETER Run
    If set, invokes pyinstaller with the bundled spec.

.PARAMETER Clean
    If set with -Run, removes build/pyinstaller and dist/TimbralInstrumentalHomogeneity under repo root first.

.NOTES
    After a successful build, refreshes:
      Homogeneity_analyser_install\portable\
    with the onedir application only (no tests, caches, or repo sources).
    PyInstaller intermediates remain under build\ and dist\ (gitignored).
#>
param(
    [switch] $Run,
    [switch] $Clean
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path (Join-Path $PSScriptRoot "..") "..")
$InstallRoot = Join-Path $RepoRoot "Homogeneity_analyser_install"
Set-Location $RepoRoot

$Spec = Join-Path $RepoRoot "packaging\windows\homogeneity_analyser_win.spec"
if (-not (Test-Path $Spec)) {
    throw "Spec not found: $Spec"
}

Write-Host "Repository root: $RepoRoot"
Write-Host "Spec: $Spec"

$pyi = Get-Command pyinstaller -ErrorAction SilentlyContinue
if (-not $pyi) {
    Write-Warning "pyinstaller not on PATH. Install with: pip install pyinstaller"
    if ($Run) { throw "pyinstaller required when -Run is set." }
    exit 0
}

$buildDir = Join-Path $RepoRoot "build\pyinstaller"
$distDir = Join-Path $RepoRoot "dist\TimbralInstrumentalHomogeneity"

if ($Clean -and $Run) {
    if (Test-Path $buildDir) { Remove-Item -Recurse -Force $buildDir }
    if (Test-Path $distDir) { Remove-Item -Recurse -Force $distDir }
}

if (-not $Run) {
    Write-Host "Dry run only. Re-run with -Run to execute PyInstaller."
    exit 0
}

& pyinstaller --clean --noconfirm $Spec
if ($LASTEXITCODE -ne 0) { throw "pyinstaller failed with exit $LASTEXITCODE" }

Write-Host "Output (onedir): $distDir"
Write-Host "Executable: $(Join-Path $distDir 'TimbralInstrumentalHomogeneity.exe')"

# --- Distribution drop folder (user-facing only; not build cache) ---
New-Item -ItemType Directory -Force $InstallRoot | Out-Null
$portableOut = Join-Path $InstallRoot "portable"
if (Test-Path $portableOut) {
    Remove-Item -LiteralPath $portableOut -Recurse -Force
}
New-Item -ItemType Directory -Force $portableOut | Out-Null
$robolog = Join-Path $env:TEMP "homogeneity_robocopy_$([Guid]::NewGuid().ToString('n')).log"
& robocopy.exe $distDir $portableOut /MIR /NFL /NDL /NJH /NJS /LOG:$robolog
$rc = $LASTEXITCODE
if ($rc -ge 8) {
    Get-Content $robolog -ErrorAction SilentlyContinue | Write-Host
    throw "robocopy failed with exit $rc (see log: $robolog)"
}
Remove-Item -Force $robolog -ErrorAction SilentlyContinue
Copy-Item -Force (Join-Path $PSScriptRoot "portable_README_FOR_DIST.txt") (Join-Path $portableOut "README_PORTABLE.txt")
Write-Host "Portable bundle: $portableOut"
Write-Host "Installer output (run build_inno.ps1 -Run): $(Join-Path $InstallRoot 'TimbralInstrumentalHomogeneitySetup.exe')"
