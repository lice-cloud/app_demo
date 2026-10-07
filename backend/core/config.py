import os
import platform
from pathlib import Path

from backend import __version__ as CURRENT_VERSION

APP_NAME = "app_demo"
COMPANY_NAME = "lice-cloud"

# GitHub 仓库（owner/repo），更新源基于 Releases
GITHUB_REPO = "lice-cloud/app_demo"

# 更新源地址（GitHub Releases latest/download 始终指向最新 Release）
UPDATE_URLS = [
    f"https://github.com/{GITHUB_REPO}/releases/latest/download/"
]


def get_app_data_dir() -> Path:
    """返回跨平台的用户数据目录（用于下载/暂存更新）。

    - Windows: %LOCALAPPDATA%\\<APP_NAME>\\updater
    - Linux/macOS: $XDG_DATA_HOME / ~/.local/share/<APP_NAME>/updater
    """
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    elif system == "Darwin":
        base = str(Path.home() / "Library" / "Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / APP_NAME / "updater"


# 运行时数据目录（下载包、暂存目录、辅助脚本）
APP_DATA_DIR = get_app_data_dir()
PYU_DATA_DIR = APP_DATA_DIR
