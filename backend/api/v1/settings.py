from fastapi import APIRouter

from backend import __version__
from backend.core.config import APP_NAME, GITHUB_REPO

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
def get_settings():
    """返回应用基础信息与更新源配置（演示新增业务模块）。"""
    return {
        "app_name": APP_NAME,
        "version": __version__,
        "update_repo": GITHUB_REPO,
        "auto_check_on_startup": True,
    }
