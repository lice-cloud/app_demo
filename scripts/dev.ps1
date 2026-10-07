# app_demo 开发一键启动脚本 (Windows)
# 用法: .\scripts\dev.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "[dev] 启动前端 Vite dev server..." -ForegroundColor Cyan
$frontend = Start-Process -FilePath "E:\nodejs\npm.cmd" -ArgumentList "run", "dev" `
    -WorkingDirectory "$Root\frontend" -PassThru -NoNewWindow

Write-Host "[dev] 等待 Vite 就绪..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

Write-Host "[dev] 启动后端 (开发模式)..." -ForegroundColor Cyan
try {
    python "$Root\backend\main.py" --dev
}
finally {
    Write-Host "[dev] 关闭前端进程..." -ForegroundColor Yellow
    if ($frontend -and -not $frontend.HasExited) {
        Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue
    }
}