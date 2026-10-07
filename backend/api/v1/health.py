import sys
from pathlib import Path

# 确保能导入 backend 包
_sys_path = Path(__file__).resolve().parent.parent.parent.parent
if str(_sys_path) not in sys.path:
    sys.path.insert(0, str(_sys_path))

from fastapi import APIRouter
from backend import __version__

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("")
def health():
    """健康检查接口，返回当前版本和平台信息。"""
    return {
        "status": "ok",
        "version": __version__,
        "platform": sys.platform,
        "python_version": sys.version.split(" ")[0],
    }