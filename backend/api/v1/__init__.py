"""v1 API 聚合层。

所有 v1 版本的路由在此统一挂载，并共享 `/api/v1` 前缀。
新增业务模块时，只需在此文件 import 并 include_router 即可，
无需改动 main.py。

注意：为避免多层 include_router 在某些 FastAPI 版本下无法展开，
版本前缀 `/api/v1` 统一在 include_router 时通过 prefix 参数施加，
子路由只声明各自的业务前缀（如 /health、/update）。
"""
from fastapi import APIRouter

from backend.api.v1.health import router as health_router
from backend.api.v1.settings import router as settings_router
from backend.api.v1.update import router as update_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/api/v1")
api_router.include_router(settings_router, prefix="/api/v1")
api_router.include_router(update_router, prefix="/api/v1")

__all__ = ["api_router"]
