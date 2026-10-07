"""Windows 下为 pywebview 窗口设置任务栏/窗口图标。

pywebview 的 create_window 不支持跨平台的图标参数，在 Windows 上
任务栏按钮默认不会使用 exe 图标，因此需要运行时通过 Win32 API
（SendMessage WM_SETICON）显式把应用图标设到窗口的小图标上。
"""
import ctypes
import sys
from ctypes import wintypes
from pathlib import Path

import webview

# Windows 常量
ICON_SMALL = 0
ICON_BIG = 1
WM_SETICON = 0x0080
IMAGE_ICON = 1
LR_LOADFROMFILE = 0x00000010
LR_DEFAULTSIZE = 0x00000040
LR_SHARED = 0x00008000


def _icon_path() -> "Path | None":
    """定位运行时可用的 icon.ico。"""
    candidates = []
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        candidates.append(base / "icon.ico")
        candidates.append(Path(sys.executable).parent / "icon.ico")
    # 开发/仓库内：backend/core/win_icon.py -> 仓库根
    repo_root = Path(__file__).resolve().parents[2]
    candidates.append(repo_root / "build" / "icon.ico")
    for c in candidates:
        if c.is_file():
            return c
    return None


def _get_hwnd(window):
    """兼容 edgechromium（HWND 为 int）与 winforms（Form.Handle）后端。"""
    nw = getattr(window, "_native_window", None)
    if nw is None:
        return None
    if isinstance(nw, int):
        return nw
    handle = getattr(nw, "Handle", None)
    if handle is not None:
        try:
            return int(handle)
        except Exception:
            return None
    return None


def set_window_icon():
    """为所有 pywebview 窗口设置图标（仅 Windows 生效）。"""
    if sys.platform != "win32":
        return
    icon = _icon_path()
    if not icon:
        return

    user32 = ctypes.windll.user32
    user32.LoadImageW.argtypes = [
        wintypes.HINSTANCE,
        wintypes.LPCWSTR,
        wintypes.UINT,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.UINT,
    ]
    user32.LoadImageW.restype = wintypes.HANDLE
    user32.SendMessageW.argtypes = [
        wintypes.HWND,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
    ]
    user32.SendMessageW.restype = wintypes.LRESULT

    # LR_SHARED 让系统托管该图标，无需手动 DestroyIcon
    flags = LR_LOADFROMFILE | LR_DEFAULTSIZE | LR_SHARED
    hicon = user32.LoadImageW(0, str(icon), IMAGE_ICON, 0, 0, flags)
    if not hicon:
        return

    for window in webview.windows:
        hwnd = _get_hwnd(window)
        if hwnd:
            # 任务栏使用小图标，标题栏/alt-tab 使用大图标
            user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
            user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
