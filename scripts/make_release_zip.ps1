# Build a clean source ZIP (no .venv, caches, or egg-info).
# Requires: git in PATH, run from repository root.
param(
    [string]$OutZip = "homogeneity_analyser_release.zip"
)
$ErrorActionPreference = "Stop"
if (-not (Test-Path ".git")) {
    Write-Error "Run from git repository root."
}
if (Test-Path $OutZip) { Remove-Item $OutZip -Force }
git archive --format=zip -o $OutZip HEAD
Write-Host "Wrote $OutZip"
