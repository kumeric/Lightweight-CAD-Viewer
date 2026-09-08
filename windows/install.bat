@echo off
REM Creates Desktop and Start Menu shortcuts for CADViewer.exe.
REM Double-click this file after extracting the CADViewer-windows.zip release
REM (install.bat, Create-Shortcut.ps1, and CADViewer.exe must be in the same folder).

setlocal
set "SCRIPT_DIR=%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%Create-Shortcut.ps1"

echo.
pause
