@echo off
setlocal
cd /d "%~dp0"

if not exist "pyproject.toml" (
    echo This script must stay next to pyproject.toml ^(repository root^).
    pause
    exit /b 1
)

echo Starting Homogeneity Analyser ^(Gradio^)...
echo Install once if needed: pip install -r requirements.txt
echo.

python -m homogeneity_analyser
set "RC=%ERRORLEVEL%"
if %RC% neq 0 (
    echo.
    echo Exit code: %RC%
    echo If "No module named homogeneity_analyser", run: pip install -r requirements.txt
    pause
)
exit /b %RC%
