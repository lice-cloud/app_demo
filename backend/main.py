import os
import socket
import threading
import time
import sys
import traceback
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import webview

from backend import __version__
from backend.core.config import APP_NAME
from backend.api import api_router
from backend.core.updater import updater, set_exit_callback

# 打包后资源目录（PyInstaller 使用 sys._MEIPASS 解压目录）
def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        # 打包后：main.exe 所在目录 / 解压目录
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).parent


BASE_DIR = get_base_dir()
WEB_DIST = BASE_DIR / "web_dist"


def _debug_log(msg: str):
    """将启动期关键信息写入 exe 同目录的 app_demo_debug.log，便于排查冻结后问题。"""
    try:
        log_path = Path(sys.executable).parent / "app_demo_debug.log"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except Exception:
        pass


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


app = FastAPI(title=APP_NAME, version=__version__)
app.include_router(api_router)


# 生产模式：挂载静态资源并托管 SPA 入口
if WEB_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(WEB_DIST / "assets")), name="assets")

    @app.get("/")
    def index():
        return FileResponse(str(WEB_DIST / "index.html"))

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str):
        # 不拦截 API / 文档等前缀，避免返回 index.html 掩盖后端错误
        if full_path.startswith(("api", "docs", "openapi.json", "redoc")):
            raise HTTPException(status_code=404, detail="Not Found")
        # 优先返回静态文件，否则回退到 index.html（支持前端路由）
        target = WEB_DIST / full_path
        if target.is_file():
            return FileResponse(str(target))
        return FileResponse(str(WEB_DIST / "index.html"))


def run_update_check():
    """启动时延迟 3 秒后自动检查更新。"""
    time.sleep(3)
    try:
        result = updater.check_for_update()
        print(f"[Updater] 启动检查结果: {result}")
    except Exception as e:
        print(f"[Updater] 启动检查失败: {e}")


def main(*, dev_mode: bool = False):
    # 0. 核对待应用更新（若上次更新已生效则清理暂存）
    updater.reconcile_pending_on_startup()

    # 记录已注册路由，便于排查“无法连接后端”
    _debug_log("Routes: " + ", ".join(sorted(r.path for r in app.routes if hasattr(r, "path"))))

    # 1. 启动 uvicorn 线程
    port = find_free_port()

    def _run_server():
        try:
            config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="info")
            server = uvicorn.Server(config)
            server.run()
        except Exception:
            _debug_log("uvicorn crashed:\n" + traceback.format_exc())

    server_thread = threading.Thread(target=_run_server, daemon=True)
    server_thread.start()

    # 等 FastAPI 就绪
    time.sleep(1)
    print(f"[Main] FastAPI: http://127.0.0.1:{port}")

    # 2. 启动时自动检查更新（后台线程，延迟 3s）
    threading.Thread(target=run_update_check, daemon=True).start()

    # 3. 决定窗口加载地址
    if dev_mode:
        url = "http://127.0.0.1:5173"
    elif WEB_DIST.exists():
        url = f"http://127.0.0.1:{port}/"
    else:
        url = "http://127.0.0.1:5173"
        print("[Main] 未找到 web_dist，回退到开发模式")

    # 4. 创建窗口并启动
    window = webview.create_window(
        title=f"{APP_NAME} v{__version__}",
        url=url,
        width=1200,
        height=800,
        min_size=(900, 600),
    )

    def _request_exit():
        """供更新完成后重启调用：关闭窗口并确保进程退出。"""
        try:
            window.destroy()
        except Exception:
            pass

        def _force():
            time.sleep(2)
            os._exit(0)

        threading.Thread(target=_force, daemon=True).start()

    set_exit_callback(_request_exit)

    def _apply_window_icon():
        """运行时为窗口设置图标（Windows 任务栏/标题栏）。"""
        try:
            from backend.core.win_icon import set_window_icon

            set_window_icon()
        except Exception as e:
            _debug_log(f"设置窗口图标失败: {e}")

    webview.start(_apply_window_icon)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="app_demo 桌面应用")
    parser.add_argument("--dev", action="store_true", help="开发模式，加载 vite dev server")
    args = parser.parse_args()
    main(dev_mode=args.dev)