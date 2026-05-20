@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist "pyproject.toml" (
    echo Keep run.bat in the repository root ^(next to pyproject.toml^).
    pause
    exit /b 1
)

set "PYTHONPATH=%CD%\src"
if not defined HOMOGENEITY_CACHE_DIR (
    set "HOMOGENEITY_CACHE_DIR=%LOCALAPPDATA%\Orchomogeneity\exports"
)
if not exist "%HOMOGENEITY_CACHE_DIR%" mkdir "%HOMOGENEITY_CACHE_DIR%" 2>nul

rem Quick dependency check (first run only installs; then starts Gradio + browser)
python -c "import gradio, homogeneity_analyser" 2>nul
if errorlevel 1 (
    echo First run: installing libraries ^(one time, may take a few minutes^)...
    python -m pip install -q -r requirements-install.txt
    if errorlevel 1 (
        echo Install failed. Try: pip install -r requirements-install.txt
        pause
        exit /b 1
    )
)

python "%~dp0packaging\windows\launcher.py"
set "RC=%ERRORLEVEL%"
if %RC% neq 0 pause
exit /b %RC%
