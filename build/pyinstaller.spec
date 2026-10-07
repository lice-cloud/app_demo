# -*- mode: python ; coding: utf-8 -*-
# app_demo PyInstaller 打包配置 (Windows 优先验证)
# 用法:
#   cd app_demo
#   pyinstaller build/pyinstaller.spec --noconfirm
#
# 说明：
#   - onedir 模式（推荐配合增量更新/全量更新）
#   - 将 backend/web_dist 前端构建产物一并打包
#   - 产物输出到 dist/app_demo/

import os
from pathlib import Path

# 项目根目录（build/ 的上一级）
ROOT = Path(SPECPATH).parent
BACKEND = ROOT / "backend"
WEB_DIST = BACKEND / "web_dist"

block_cipher = None

# 数据文件：前端构建产物
datas = []
if WEB_DIST.exists():
    datas.append((str(WEB_DIST), "web_dist"))

# 隐式导入（FastAPI/uvicorn/pywebview 常见子模块）
hiddenimports = [
    "uvicorn",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "webview",
    "webview.platforms",
    "webview.platforms.edgechromium",
    "webview.platforms.winforms",
    "clr_loader",
    "pythonnet",
    "anyio",
    "anyio._backends._asyncio",
    "backend",
    "backend.core",
    "backend.core.config",
    "backend.core.updater",
    "backend.api",
    "backend.api.v1",
    "backend.api.v1.health",
    "backend.api.v1.settings",
    "backend.api.v1.update",
]

a = Analysis(
    [str(BACKEND / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy", "pandas"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="app_demo",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 桌面应用不显示控制台窗口
    disable_windowed_traceback=False,
    icon=str(ROOT / "build" / "icon.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="app_demo",
)
