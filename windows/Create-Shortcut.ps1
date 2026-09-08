# Creates Desktop and Start Menu shortcuts (with the CAD Viewer icon) for CADViewer.exe.
# Run this after placing Create-Shortcut.ps1 (or install.bat) in the SAME folder as CADViewer.exe.
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$exePath = Join-Path $scriptDir "CADViewer.exe"

if (-not (Test-Path $exePath)) {
    Write-Host "ERROR: CADViewer.exe was not found in $scriptDir" -ForegroundColor Red
    Write-Host "Place this script in the same folder as CADViewer.exe and run it again." -ForegroundColor Red
    exit 1
}

$WshShell = New-Object -ComObject WScript.Shell

function New-CadViewerShortcut($linkPath) {
    $shortcut = $WshShell.CreateShortcut($linkPath)
    $shortcut.TargetPath = $exePath
    $shortcut.WorkingDirectory = $scriptDir
    $shortcut.IconLocation = "$exePath,0"
    $shortcut.Description = "Lightweight CAD Viewer (STL/OBJ/PLY/STEP/IGES)"
    $shortcut.Save()
    Write-Host "Created: $linkPath" -ForegroundColor Green
}

$desktop = [Environment]::GetFolderPath("Desktop")
New-CadViewerShortcut (Join-Path $desktop "CAD Viewer.lnk")

$startMenuPrograms = Join-Path ([Environment]::GetFolderPath("StartMenu")) "Programs"
New-CadViewerShortcut (Join-Path $startMenuPrograms "CAD Viewer.lnk")

Write-Host ""
Write-Host "Done. You can now launch CAD Viewer from the Desktop icon or the Start Menu." -ForegroundColor Cyan
