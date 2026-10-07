"""Windows 任务栏/窗口图标设置辅助。

pywebview 的 WinForms 后端会在创建窗口时读取 _state['icon'] 设置 Form.Icon，
因此主流程通过 webview.start(icon=...) 传入图标路径即可。
此处额外提供运行时 Win32 兜底：在窗口创建后向窗口发送 WM_SETICON，
确保即使在个别环境下 Form.Icon 未生效，任务栏图标也能正确显示。
"""
import ctypes
import sys
from pathlib import Path

import webview

ICON_SMALL = 0
ICON_BIG = 1
WM_SETICON = 0x0080
IMAGE_ICON = 1
LR_LOADFROMFILE = 0x00000010
LR_DEFAULTSIZE = 0x00000040
LR_SHARED = 0x00008000


def _icon_path() -> "Path | None":
    """定位运行时可用的 icon.ico。

    打包后优先从 sys._MEIPASS / exe 目录查找（与 PyInstaller datas 中 target='.' 对应）；
    开发时回退到仓库根目录 build/icon.ico。
    """
    candidates = []
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        candidates.append(base / "icon.ico")
        candidates.append(Path(sys.executable).parent / "icon.ico")
    # 开发：backend/core/win_icon.py -> 仓库根
    repo_root = Path(__file__).resolve().parents[2]
    candidates.append(repo_root / "build" / "icon.ico")
    for c in candidates:
        if c.is_file():
            return c
    return None


def _get_hwnd(window):
    """兼容 edgechromium（HWND 为 int）与 winforms（Form 对象）后端。"""
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
    # 注意：ctypes.wintypes 没有 LRESULT，用 c_void_p 代替返回/参数类型即可
    user32.LoadImageW.argtypes = [
        ctypes.c_void_p,
        ctypes.c_wchar_p,
        ctypes.c_uint,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_uint,
    ]
    user32.LoadImageW.restype = ctypes.c_void_p
    user32.SendMessageW.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint,
        ctypes.c_void_p,
        ctypes.c_void_p,
    ]
    user32.SendMessageW.restype = ctypes.c_void_p

    # LR_SHARED 让系统托管图标，无需手动 DestroyIcon
    flags = LR_LOADFROMFILE | LR_DEFAULTSIZE | LR_SHARED
    hicon_big = user32.LoadImageW(0, str(icon), IMAGE_ICON, 32, 32, flags)
    hicon_small = user32.LoadImageW(0, str(icon), IMAGE_ICON, 16, 16, flags)
    if not hicon_big and not hicon_small:
        return

    for window in webview.windows:
        hwnd = _get_hwnd(window)
        if hwnd:
            if hicon_big:
                user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_big)
            if hicon_small:
                user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_small)
