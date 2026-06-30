#Requires -Version 5.1
<#
.SYNOPSIS
    Build only the PyInstaller onedir bundle (no Inno Setup).

.DESCRIPTION
    Wraps build_pyinstaller.ps1 -Run. Output:
      dist\TimbralInstrumentalHomogeneity\TimbralInstrumentalHomogeneity.exe

    From repository root:
      .\packaging\windows\build_windows.ps1
      .\packaging\windows\build_windows.ps1 -Clean   # wipe prior build\pyinstaller and dist\TimbralInstrumentalHomogeneity first

    Prerequisites: pip install -e ".[dev]" ; pip install pyinstaller
#>
param(
    [switch] $Clean
)

$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
$child = Join-Path $here "build_pyinstaller.ps1"
if (-not (Test-Path $child)) {
    throw "Missing sibling script: $child"
}
if ($Clean) {
    & $child -Run -Clean
} else {
    & $child -Run
}
