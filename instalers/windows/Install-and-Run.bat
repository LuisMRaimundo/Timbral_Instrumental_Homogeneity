@echo off
setlocal EnableExtensions
title Timbral_Instrumental_Homogeneity

cd /d "%~dp0..\.." || (
  echo ERROR: Cannot find project root.
  pause
  exit /b 1
)
set "ROOT=%CD%"
set "PY=%ROOT%\instalers\runtime\windows\python\python.exe"
set "BOOT=%ROOT%\instalers\common\bootstrap.py"
set "SETUP=%ROOT%\instalers\windows\setup.ps1"
set "LOG=%ROOT%\instalers\runtime\windows\install.log"

echo.
echo  Timbral_Instrumental_Homogeneity (cloned repo)
echo  =====================================
echo.
echo  For ZIP-only users, use INSTALL.bat instead.
echo.

if not exist "%BOOT%" (
  echo No bootstrap found - starting INSTALL.bat for standard install...
  call "%~dp0INSTALL.bat"
  exit /b %ERRORLEVEL%
)

if not exist "%PY%" (
  echo First run: installing portable Python and libraries...
  echo Internet connection required. This may take several minutes.
  echo Log: %LOG%
  echo.
  if not exist "%SETUP%" (
    echo ERROR: setup.ps1 not found at:
    echo   %SETUP%
    pause
    exit /b 1
  )
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SETUP%"
  if errorlevel 1 (
    echo.
    echo Setup failed. See log:
    echo   %LOG%
    pause
    exit /b 1
  )
)

if not exist "%PY%" (
  echo ERROR: Portable Python was not installed.
  echo See log: %LOG%
  pause
  exit /b 1
)

"%PY%" "%BOOT%" launch
set "EXITCODE=%ERRORLEVEL%"
echo.
if not "%EXITCODE%"=="0" echo The app exited with code %EXITCODE%.
echo You can close this window.
pause
exit /b %EXITCODE%
