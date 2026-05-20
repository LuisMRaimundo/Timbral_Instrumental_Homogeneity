@echo off
REM Optional wrapper: copy next to HomogeneityAnalyser.exe after PyInstaller COLLECT output.
cd /d "%~dp0"
start "" "%~dp0HomogeneityAnalyser.exe"
