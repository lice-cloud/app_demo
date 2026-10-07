import sys

from fastapi import APIRouter
from backend import __version__

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health():
    """健康检查接口，返回当前版本和平台信息。"""
    return {
        "status": "ok",
        "version": __version__,
        "platform": sys.platform,
        "python_version": sys.version.split(" ")[0],
    }