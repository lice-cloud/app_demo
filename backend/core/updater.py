import json
import hashlib
import platform
import shutil
import sys
import tarfile
import threading
import urllib.request
import urllib.error
import zipfile
from pathlib import Path
from typing import Callable, Dict, Any, Optional

from backend import __version__ as CURRENT_VERSION

import os

from backend.core.config import GITHUB_REPO, APP_DATA_DIR as PYU_DATA_DIR

# GitHub API 与下载地址（可通过环境变量覆盖，便于本地测试）
GITHUB_API = os.environ.get(
    "APP_DEMO_UPDATE_API",
    f"https://api.github.com/repos/{GITHUB_REPO}/releases",
)
GITHUB_DOWNLOAD = os.environ.get(
    "APP_DEMO_UPDATE_DOWNLOAD",
    f"https://github.com/{GITHUB_REPO}/releases/latest/download",
)

USER_AGENT = f"app_demo/{CURRENT_VERSION}"


# ──────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────

def _parse_version(v: str) -> tuple:
    """将 '0.1.2' 解析为可比较的元组。忽略 v 前缀。"""
    v = v.lstrip("v").strip()
    parts = []
    for p in v.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def _http_get_json(url: str, timeout: int = 15) -> Optional[list]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[Updater] HTTP GET failed: {url} -> {e}")
        return None


def _platform_keywords() -> tuple:
    """返回当前平台匹配更新资产的关键词列表。"""
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "windows":
        return ("win", "windows", ".exe", ".zip")
    if system == "linux":
        if "arm" in machine or "aarch64" in machine:
            return ("linux-arm", "linux_arm", "arm64", "aarch64", ".tar.gz")
        return ("linux", "linux-x64", "linux_x64", ".tar.gz")
    if system == "darwin":
        return ("mac", "macos", "darwin", ".dmg", ".zip")
    return (system,)


def _select_asset(assets: list) -> Optional[dict]:
    """从 Release 资产中选择适合当前平台的更新包。"""
    keywords = _platform_keywords()
    # 优先精确匹配平台关键词
    for kw in keywords:
        for asset in assets:
            if kw in asset.get("name", "").lower():
                return asset
    # 回退：第一个压缩包类资产
    for asset in assets:
        name = asset.get("name", "").lower()
        if name.endswith((".zip", ".tar.gz", ".tgz")):
            return asset
    return assets[0] if assets else None


# ──────────────────────────────────────────────
# 进度跟踪
# ──────────────────────────────────────────────

class ProgressTracker:
    def __init__(self):
        self._lock = threading.Lock()
        self._state: Dict[str, Any] = {
            "phase": "idle",
            "percent": 0,
            "bytes_done": 0,
            "bytes_total": 0,
            "message": "",
            "error": None,
        }

    def set(self, **kwargs):
        with self._lock:
            self._state.update(kwargs)

    def get(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._state)

    def reset(self):
        with self._lock:
            self._state = {
                "phase": "idle",
                "percent": 0,
                "bytes_done": 0,
                "bytes_total": 0,
                "message": "",
                "error": None,
            }


_progress = ProgressTracker()


# ──────────────────────────────────────────────
# Updater
# ──────────────────────────────────────────────

class Updater:
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir) if data_dir else Path(PYU_DATA_DIR)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._update_in_progress = False
        self._latest_release: Optional[Dict[str, Any]] = None

    @property
    def staging_dir(self) -> Path:
        return self.data_dir / "staging"

    @property
    def pending_file(self) -> Path:
        return self.data_dir / "pending_update.json"

    # ── 检查更新 ──
    def check_for_update(self) -> Dict[str, Any]:
        empty = {
            "current_version": CURRENT_VERSION,
            "has_update": False,
            "latest_version": None,
            "notes": None,
            "release_url": None,
        }

        releases = _http_get_json(GITHUB_API)
        if not releases or not isinstance(releases, list):
            return empty

        # 找最新非草稿、非预发布版本
        latest = None
        for rel in releases:
            if rel.get("draft") or rel.get("prerelease"):
                continue
            latest = rel
            break
        if latest is None:
            return empty

        self._latest_release = latest
        latest_version = latest.get("tag_name", "").lstrip("v")
        has_update = _parse_version(latest_version) > _parse_version(CURRENT_VERSION)

        if not has_update:
            return {
                "current_version": CURRENT_VERSION,
                "has_update": False,
                "latest_version": latest_version,
                "notes": latest.get("body"),
                "release_url": None,
            }

        asset = _select_asset(latest.get("assets", []))
        release_url = asset.get("browser_download_url") if asset else None

        return {
            "current_version": CURRENT_VERSION,
            "has_update": True,
            "latest_version": latest_version,
            "notes": latest.get("body") or "暂无更新说明",
            "release_url": release_url,
        }

    # ── 应用更新 ──
    def apply_update(self, progress_callback: Optional[Callable] = None) -> Optional[threading.Thread]:
        with self._lock:
            if self._update_in_progress:
                return None
            self._update_in_progress = True

        thread = threading.Thread(
            target=self._apply_worker,
            args=(progress_callback,),
            daemon=True,
        )
        thread.start()
        return thread

    def _apply_worker(self, progress_callback: Optional[Callable]):
        try:
            _progress.reset()
            _progress.set(phase="checking", message="检查更新...")

            # 重新确认有新版本
            rel = self._latest_release
            if rel is None:
                result = self.check_for_update()
                if not result["has_update"]:
                    _progress.set(phase="error", message="当前已是最新版本", error="no_update")
                    return
                rel = self._latest_release

            asset = _select_asset(rel.get("assets", []))
            if asset is None:
                _progress.set(phase="error", message="未找到可下载的更新包", error="no_asset")
                return

            url = asset["browser_download_url"]
            self._download_and_install(url, asset.get("name", "update.zip"), progress_callback)

        except Exception as e:
            import traceback
            traceback.print_exc()
            _progress.set(phase="error", message=f"更新失败: {e}", error=str(e))
        finally:
            with self._lock:
                self._update_in_progress = False

    def _download_and_install(self, url: str, filename: str,
                              progress_callback: Optional[Callable]):
        download_path = self.data_dir / filename

        # 下载
        _progress.set(phase="downloading", percent=0, message="开始下载...")
        self._download(url, download_path, progress_callback)

        # 校验（大小校验；若资产提供 digest 可在后续增强）
        _progress.set(phase="verifying", percent=100, message="校验下载文件...")
        if not download_path.exists() or download_path.stat().st_size == 0:
            _progress.set(phase="error", message="下载文件为空", error="empty_download")
            return

        # 解压到临时目录
        tmp_extract = self.data_dir / "extract_tmp"
        if tmp_extract.exists():
            shutil.rmtree(tmp_extract, ignore_errors=True)
        tmp_extract.mkdir(parents=True, exist_ok=True)

        _progress.set(phase="installing", percent=40, message="解压更新包...")
        try:
            if download_path.name.endswith(".zip"):
                with zipfile.ZipFile(download_path) as zf:
                    zf.extractall(tmp_extract)
            else:
                with tarfile.open(download_path, "r:gz") as tf:
                    tf.extractall(tmp_extract)
        except Exception as e:
            _progress.set(phase="error", message=f"解压失败: {e}", error=str(e))
            return

        # 归一化：若压缩包内只有单一顶层目录，则以其内容为根
        source_root = self._normalize_root(tmp_extract)

        # 组装暂存目录（其内容即最终应放入安装目录的文件）
        if self.staging_dir.exists():
            shutil.rmtree(self.staging_dir, ignore_errors=True)
        self.staging_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_root, self.staging_dir)
        shutil.rmtree(tmp_extract, ignore_errors=True)
        download_path.unlink(missing_ok=True)

        app_dir = self._get_app_dir()

        if getattr(sys, "frozen", False):
            # 冻结环境：写入待应用标记，重启时由辅助进程替换被占用的文件
            self._write_pending(app_dir)
            _progress.set(
                phase="ready", percent=100,
                message="更新已就绪，重启应用以完成安装",
                error=None,
            )
        else:
            # 开发环境：文件未被占用，直接复制
            _progress.set(phase="installing", percent=70, message="应用更新...")
            replaced = self._replace_files(self.staging_dir, app_dir)
            shutil.rmtree(self.staging_dir, ignore_errors=True)
            if replaced:
                _progress.set(phase="done", percent=100,
                              message="更新完成，请重启应用", error=None)
            else:
                _progress.set(phase="error", percent=0,
                              message="更新包中没有可替换的文件", error="no_files")

    @staticmethod
    def _normalize_root(root: Path) -> Path:
        """若目录中只有一个可见子目录，则将其视为真正的根。"""
        entries = [e for e in root.iterdir() if not e.name.startswith(".")]
        if len(entries) == 1 and entries[0].is_dir():
            return entries[0]
        return root

    # ── 待应用更新（冻结环境） ──
    def _write_pending(self, app_dir: Path):
        info = {
            "staging": str(self.staging_dir),
            "target": str(app_dir),
            "exe": str(Path(sys.executable)),
            "version": (self._latest_release or {}).get("tag_name"),
        }
        self.pending_file.write_text(
            json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def has_pending_update(self) -> bool:
        return self.pending_file.exists() and self.staging_dir.exists()

    def clear_pending(self):
        try:
            self.pending_file.unlink(missing_ok=True)
        except Exception:
            pass
        shutil.rmtree(self.staging_dir, ignore_errors=True)

    def reconcile_pending_on_startup(self):
        """启动时核对待应用更新是否已生效，避免重复应用。

        若当前版本已达到待更新版本，说明辅助进程已成功替换文件，清理标记；
        否则保留标记，等待用户重试。
        """
        if not self.pending_file.exists():
            return
        try:
            info = json.loads(self.pending_file.read_text(encoding="utf-8"))
        except Exception:
            self.clear_pending()
            return
        pending_ver = (info.get("version") or "").lstrip("v")
        if pending_ver and _parse_version(CURRENT_VERSION) >= _parse_version(pending_ver):
            print(f"[Updater] 更新已生效 ({CURRENT_VERSION})，清理暂存")
            self.clear_pending()
        else:
            print(f"[Updater] 检测到未完成的更新 (目标 {pending_ver})，保留暂存以便重试")

    def apply_pending_and_restart(self, exit_callback: Optional[Callable] = None) -> bool:
        """启动辅助进程完成文件替换，然后退出当前应用。

        辅助进程会等待当前进程结束后再复制文件，从而绕过 Windows 对
        正在运行的 exe / DLL 的文件锁。
        """
        if not self.has_pending_update():
            return False
        try:
            info = json.loads(self.pending_file.read_text(encoding="utf-8"))
        except Exception:
            return False

        staging = info["staging"]
        target = info["target"]
        exe = info["exe"]
        pid = os.getpid()

        import subprocess

        if platform.system() == "Windows":
            helper = self._create_windows_helper(pid, staging, target, exe)
            # 注意：不能使用 DETACHED_PROCESS（无控制台会使 helper 中的
            # tasklist/find/ping 等命令无法正常执行）。CREATE_NO_WINDOW 可隐藏
            # 窗口且仍能独立于父进程存活。
            CREATE_NO_WINDOW = 0x08000000
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            subprocess.Popen(
                ["cmd", "/c", str(helper)],
                creationflags=CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP,
                close_fds=True,
            )
        else:
            helper = self._create_posix_helper(pid, staging, target, exe)
            subprocess.Popen(
                ["/bin/sh", str(helper)],
                start_new_session=True,
                close_fds=True,
            )

        if exit_callback:
            exit_callback()
        return True

    def _create_windows_helper(self, pid: int, staging: str,
                               target: str, exe: str) -> Path:
        helper = self.data_dir / "apply_update.cmd"
        lines = [
            "@echo off",
            "setlocal",
            f'set "PID={pid}"',
            f'set "SRC={staging}"',
            f'set "DST={target}"',
            f'set "EXE={exe}"',
            "",
            ":waitloop",
            'tasklist /FI "PID eq %PID%" /NH 2>nul | find /I "%PID%" >nul',
            "if not errorlevel 1 (",
            "    ping -n 2 127.0.0.1 >nul",
            "    goto waitloop",
            ")",
            "",
            'if exist "%SRC%" (',
            '    robocopy "%SRC%" "%DST%" /E /IS /IT /R:10 /W:1 >nul',
            ")",
            "",
            'start "" "%EXE%"',
            'del "%~f0"',
            "",
        ]
        helper.write_text("\r\n".join(lines), encoding="ascii", errors="ignore")
        return helper

    def _create_posix_helper(self, pid: int, staging: str,
                             target: str, exe: str) -> Path:
        helper = self.data_dir / "apply_update.sh"
        lines = [
            "#!/bin/sh",
            f'PID="{pid}"',
            f'SRC="{staging}"',
            f'DST="{target}"',
            f'EXE="{exe}"',
            'while kill -0 "$PID" 2>/dev/null; do sleep 1; done',
            'if [ -d "$SRC" ]; then',
            '    cp -rf "$SRC"/. "$DST"/ 2>/dev/null',
            "fi",
            '"$EXE" &',
            'rm -f "$0"',
            "",
        ]
        helper.write_text("\n".join(lines), encoding="utf-8")
        try:
            helper.chmod(0o755)
        except Exception:
            pass
        return helper

    def _download(self, url: str, dest: Path, progress_callback: Optional[Callable]):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            done = 0
            with open(dest, "wb") as f:
                while True:
                    chunk = resp.read(64 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
                    done += len(chunk)
                    percent = int(done / total * 100) if total else 0
                    _progress.set(
                        phase="downloading",
                        percent=percent,
                        bytes_done=done,
                        bytes_total=total,
                        message=f"下载中 {percent}%",
                    )
                    if progress_callback:
                        try:
                            progress_callback(_progress.get())
                        except Exception:
                            pass

    def _get_app_dir(self) -> Path:
        """获取当前应用的安装目录。"""
        if getattr(sys, "frozen", False):
            return Path(sys.executable).parent
        # 开发模式：项目根目录（backend 的上级）
        return Path(__file__).resolve().parent.parent.parent

    def _replace_files(self, source_root: Path, app_dir: Path) -> bool:
        """将暂存目录中的文件复制到应用目录（仅用于开发环境）。

        冻结环境下的文件替换由辅助进程在应用退出后完成，
        参见 apply_pending_and_restart。
        """
        replaced = False
        for src in source_root.rglob("*"):
            if not src.is_file():
                continue
            rel = src.relative_to(source_root)
            target = app_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(src, target)
                replaced = True
            except Exception as e:
                print(f"[Updater] 复制失败 {rel}: {e}")
        return replaced

    def get_progress(self) -> Dict[str, Any]:
        return _progress.get()


updater = Updater()

# ── 应用退出回调（由 main.py 注册，供 restart 接口调用） ──
_exit_callback: Optional[Callable] = None


def set_exit_callback(cb: Optional[Callable]):
    global _exit_callback
    _exit_callback = cb


def get_exit_callback() -> Optional[Callable]:
    return _exit_callback


# ── 模块级函数（供 API 直接调用） ──
def get_progress() -> Dict[str, Any]:
    return _progress.get()
