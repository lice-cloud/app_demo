"""应用图标定位辅助（用于 pywebview / PyInstaller 运行时）。"""
import sys
from pathlib import Path


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
