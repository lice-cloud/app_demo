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

# 运行时窗口图标（Windows 任务栏/标题栏图标，运行时由 Win32 设置）
ICON_SRC = ROOT / "build" / "icon.ico"
if ICON_SRC.exists():
    datas.append((str(ICON_SRC), "."))

# Linux/macOS 窗口图标：GTK/AppKit 需要 png，.ico 在 Linux 下 gdk-pixbuf 无法加载
ICON_PNG = ROOT / "build" / "icon.png"
if ICON_PNG.exists():
    datas.append((str(ICON_PNG), "."))

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
    # Linux 后端（gtk 由 guilib 在运行时动态 import，PyInstaller 无法静态发现，必须显式声明）
    "webview.platforms.gtk",
    # Windows 后端
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

# 剔除 GTK 自带、但 webview 应用用不到的图标/窗口主题数据（约 225M 未压缩）。
# 这些仅用于 GTK 原生控件与桌面主题，本应用 UI 是网页，缺失时会回退到内置默认，不影响功能。
_EXCLUDE_DATA_SUBSTR = ("share/icons/", "share/themes/")
a.datas = [d for d in a.datas if not any(s in d[0] for s in _EXCLUDE_DATA_SUBSTR)]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="app_demo",
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
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
    strip=True,
    upx=True,
    upx_exclude=[],
    name="app_demo",
)
