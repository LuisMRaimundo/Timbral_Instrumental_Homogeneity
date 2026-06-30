@echo off
title Timbral_Instrumental_Homogeneity - Installer
cd /d "%~dp0"

echo.
echo  *** USE THIS FILE FOR NORMAL INSTALL ***
echo.
echo  Timbral_Instrumental_Homogeneity - automatic setup
echo  (Python + libraries + shortcuts)
echo.
echo  GitHub: https://github.com/LuisMRaimundo/Timbral_Instrumental_Homogeneity
echo.
echo  Do not close this window until finished.
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-Easy.ps1"
set ERR=%ERRORLEVEL%

echo.
if %ERR% NEQ 0 (
  echo Installation failed. See install.log in:
  echo   %LOCALAPPDATA%\Programs\Timbral_Instrumental_Homogeneity\
) else (
  echo Done.
)
echo.
pause
exit /b %ERR%
