# Build app_demo release artifacts on Windows:
#   1. frontend build  -> backend/web_dist
#   2. PyInstaller     -> dist/app_demo
#   3. portable zip    -> app_demo-win-x64-<version>.zip
#   4. Inno Setup      -> dist/installer/app_demo-setup-<version>.exe (if iscc found)
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/build_release.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

# Read version
$initPy = Get-Content (Join-Path $Root "backend\__init__.py") -Raw
if ($initPy -match '__version__\s*=\s*"([^"]+)"') {
    $Version = $Matches[1]
} else {
    throw "Cannot read __version__ from backend/__init__.py"
}
Write-Host "Version: $Version"

# 1. Frontend
Write-Host "==> Building frontend"
Push-Location (Join-Path $Root "frontend")
if (-not (Test-Path "node_modules")) { npm install }
npm run build
Pop-Location

# 2. PyInstaller
Write-Host "==> Building application (PyInstaller)"
python -m PyInstaller build/pyinstaller.spec --noconfirm --distpath dist --workpath build/pyinstaller

# 3. Portable zip
Write-Host "==> Packaging portable zip"
$zip = Join-Path $Root "app_demo-win-x64-$Version.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path (Join-Path $Root "dist\app_demo") -DestinationPath $zip -Force

# 4. Inno Setup (optional)
$iscc = @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($iscc) {
    Write-Host "==> Building installer with Inno Setup"
    & $iscc "/DMyAppVersion=$Version" "build\installer.iss"
} else {
    Write-Warning "Inno Setup (ISCC.exe) not found. Skipping installer."
    Write-Warning "Install it from https://jrsoftware.org/isdl.php and re-run."
}

Write-Host "Done. Artifacts:"
Get-ChildItem $Root -Filter "app_demo-*-$Version.zip" | ForEach-Object { Write-Host "  $($_.FullName)" }
if (Test-Path (Join-Path $Root "dist\installer")) {
    Get-ChildItem (Join-Path $Root "dist\installer") -Filter "*.exe" | ForEach-Object { Write-Host "  $($_.FullName)" }
}
