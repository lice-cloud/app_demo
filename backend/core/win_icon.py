"""Windows 任务栏/窗口图标设置辅助。

pywebview 在不同版本/后端下并不稳定暴露窗口句柄属性（_native_window 在新版已不存在），
因此这里不依赖 pywebview 内部结构，而是直接枚举当前进程的所有顶层窗口，
向它们发送 WM_SETICON，确保运行中的任务栏/标题栏图标显示应用图标。

同时，主流程仍通过 webview.start(icon=...) 让 pywebview 设置 Form.Icon 作为兜底。
"""
import ctypes
import os
import sys
from pathlib import Path

ICON_SMALL = 0
ICON_BIG = 1
WM_SETICON = 0x0080
IMAGE_ICON = 1
LR_LOADFROMFILE = 0x00000010
LR_DEFAULTSIZE = 0x00000040
LR_SHARED = 0x00008000
GW_OWNER = 4
GCLP_HICON = -14
GCLP_HICONSM = -34


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


def _enum_top_windows(pid: int):
    """枚举属于当前进程、无 owner 的顶层窗口（任务栏按钮所属窗口）。"""
    user32 = ctypes.windll.user32
    found = []
    WINDOWENUMPROC = ctypes.WINFUNCTYPE(
        ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p
    )

    proc_id = ctypes.c_uint32()

    def _callback(hwnd, _lparam):
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(proc_id))
        if proc_id.value == pid:
            # 顶层窗口（无 owner）才是任务栏对应的窗口
            if user32.GetWindow(hwnd, GW_OWNER) == 0:
                found.append(hwnd)
        return True

    user32.EnumWindows(WINDOWENUMPROC(_callback), 0)
    # 兜底：若没有无 owner 的窗口，退而求其次取所有本进程顶层可见窗口
    if not found:
        def _callback2(hwnd, _lparam):
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(proc_id))
            if proc_id.value == pid and user32.IsWindowVisible(hwnd):
                if user32.GetWindow(hwnd, GW_OWNER) == 0:
                    found.append(hwnd)
            return True

        user32.EnumWindows(WINDOWENUMPROC(_callback2), 0)
    return found


def set_window_icon():
    """为当前进程的顶层窗口设置图标（仅 Windows 生效）。"""
    if sys.platform != "win32":
        return
    icon = _icon_path()
    if not icon:
        return

    user32 = ctypes.windll.user32
    # 注意：ctypes.wintypes 没有 LRESULT，用 c_void_p 代替返回/参数类型
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

    hwnds = _enum_top_windows(os.getpid())
    if not hwnds:
        return

    # 同时设置窗口类图标，最大化任务栏/alt-tab 生效概率
    set_class = getattr(user32, "SetClassLongPtrW", None) or user32.SetClassLongW
    set_class.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
    set_class.restype = ctypes.c_void_p

    for hwnd in hwnds:
        if hicon_big:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_big)
            set_class(hwnd, GCLP_HICON, hicon_big)
        if hicon_small:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_small)
            set_class(hwnd, GCLP_HICONSM, hicon_small)
