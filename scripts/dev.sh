#!/usr/bin/env bash
# app_demo 开发一键启动脚本 (Linux/macOS)
# 用法: ./scripts/dev.sh

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "[dev] 启动前端 Vite dev server..."
(cd "$ROOT/frontend" && npm run dev) &
FRONTEND_PID=$!

echo "[dev] 等待 Vite 就绪..."
sleep 3

echo "[dev] 启动后端 (开发模式)..."
trap 'echo "[dev] 关闭前端进程..."; kill $FRONTEND_PID 2>/dev/null || true' EXIT
python "$ROOT/backend/main.py" --dev