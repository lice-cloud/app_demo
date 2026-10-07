import threading
import time
from fastapi import APIRouter
from backend import __version__
from backend.core.updater import (
    updater,
    get_progress,
    get_exit_callback,
    GITHUB_DOWNLOAD,
)

router = APIRouter(prefix="/update", tags=["update"])


@router.get("/check")
def check():
    """检查更新（启动时自动检查或手动点击）。

    返回：
        - current_version: 当前版本
        - has_update: 是否有新版本
        - latest_version: 最新版本号
        - notes: 更新日志（Markdown 格式）
        - release_url: 下载链接
    """
    try:
        return updater.check_for_update()
    except Exception:
        import traceback
        traceback.print_exc()
        return {
            "current_version": __version__,
            "has_update": False,
            "latest_version": None,
            "notes": None,
            "release_url": None,
        }


@router.get("/status")
def status():
    """查询更新进度快照。"""
    return get_progress()


@router.post("/apply")
def apply():
    """执行更新（下载 + 校验 + 暂存/安装）。"""
    try:
        thread = updater.apply_update()
        if thread is None:
            return {"task_started": False, "message": "已有更新任务在进行中"}
        return {"task_started": True, "message": "更新任务已在后台启动"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"task_started": False, "message": f"启动失败: {e}"}


@router.get("/pending")
def pending():
    """查询是否有已暂存、等待重启应用的更新。"""
    return {"has_pending": updater.has_pending_update()}


@router.post("/restart")
def restart():
    """应用暂存的更新并重启应用。

    冻结环境下会启动一个独立的辅助进程，等待本进程退出后替换文件并拉起新版本；
    开发环境下直接退出（文件已即时替换）。
    """
    def _do_restart():
        # 稍作延迟，确保 HTTP 响应已发送
        time.sleep(0.6)
        exit_cb = get_exit_callback()
        applied = updater.apply_pending_and_restart(exit_callback=None)
        if applied:
            print("[Updater] 已启动辅助进程，准备退出应用以完成更新")
        if exit_cb:
            exit_cb()

    threading.Thread(target=_do_restart, daemon=True).start()
    return {
        "message": "正在应用更新并重启应用...",
        "has_pending": updater.has_pending_update(),
    }
