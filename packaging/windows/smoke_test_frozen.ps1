#Requires -Version 5.1
<#
.SYNOPSIS
    Smoke-test the frozen HomogeneityAnalyser.exe (Gradio responds on localhost).

.PARAMETER ExePath
    Full path to HomogeneityAnalyser.exe (default: dist\HomogeneityAnalyser under repo root).

.PARAMETER Port
    Must match GRADIO_SERVER_PORT used by frozen_launcher (default 7860).

.PARAMETER TimeoutSeconds
    Max wait for HTTP 200 from Gradio root (default 180; cold import can be slow).
#>
param(
    [string] $ExePath = "",
    [int] $Port = 7860,
    [int] $TimeoutSeconds = 180
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path (Join-Path $PSScriptRoot "..") "..")

if (-not $ExePath) {
    $ExePath = Join-Path $RepoRoot "dist\HomogeneityAnalyser\HomogeneityAnalyser.exe"
}
if (-not (Test-Path $ExePath)) {
    throw "Executable not found: $ExePath"
}

$env:GRADIO_SERVER_PORT = "$Port"
$env:GRADIO_SERVER_NAME = "127.0.0.1"

$exeDir = Split-Path -Parent $ExePath
$p = Start-Process -FilePath $ExePath -WorkingDirectory $exeDir -PassThru -NoNewWindow
try {
    $url = "http://127.0.0.1:$Port/"
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $ok = $false
    while ((Get-Date) -lt $deadline) {
        if ($p.HasExited) {
            throw "Process exited early with code $($p.ExitCode)"
        }
        try {
            $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5
            if ($r.StatusCode -eq 200) {
                # Gradio's initial HTML shell may not include the full Blocks title verbatim; require app markers.
                if ($r.Content -notmatch "Homogeneity Analyser|H_TI|Symbolic inspection|Loaded XML inspection") {
                    throw "HTTP 200 but root page does not look like the H_TI app (wrong server on port $Port?)."
                }
                $ok = $true
                break
            }
        } catch {
            if ($_.Exception.Message -match "H_TI app|wrong server") {
                throw
            }
            Start-Sleep -Seconds 2
        }
    }
    if (-not $ok) {
        throw "Did not receive HTTP 200 from $url within $TimeoutSeconds s"
    }
    Write-Host "SMOKE OK: $url returned 200"
}
finally {
    if (-not $p.HasExited) {
        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
    }
}
