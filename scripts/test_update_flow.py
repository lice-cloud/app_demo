"""本地更新闭环测试（不依赖真实 GitHub Releases）。

模拟 GitHub Releases API，创建假的更新包，验证：
  1. 版本检查（check_for_update）
  2. 下载 + 校验 + 应用（apply_update）
  3. 文件替换是否成功

用法:
    python scripts/test_update_flow.py
"""

import json
import os
import shutil
import sys
import tempfile
import threading
import time
import zipfile
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend import __version__ as CURRENT_VERSION


def _bump_patch_version(v: str) -> str:
    """生成一个比当前版本号高 patch 一级的测试版本。"""
    parts = [int(x) for x in v.split(".")]
    parts[-1] += 1
    return ".".join(str(x) for x in parts)


# 在导入 updater 前设置环境变量，指向本地模拟服务
MOCK_PORT = 8791
os.environ["APP_DEMO_UPDATE_API"] = f"http://127.0.0.1:{MOCK_PORT}/releases"
os.environ["APP_DEMO_UPDATE_DOWNLOAD"] = f"http://127.0.0.1:{MOCK_PORT}/latest/download"


def build_fake_release(server_dir: Path, version: str):
    """在服务器目录中生成一个假的更新包和 API 响应。"""
    # 1. 构造更新包内容（模拟应用目录的一部分文件）
    pkg_root = server_dir / f"app_demo-{version}"
    (pkg_root / "backend").mkdir(parents=True, exist_ok=True)
    (pkg_root / "backend" / "new_feature.txt").write_text(
        f"这是 {version} 版本新增的文件\n", encoding="utf-8"
    )
    (pkg_root / "VERSION.txt").write_text(version, encoding="utf-8")

    # 2. 打包为 zip
    zip_name = f"app_demo-win-x64-{version}.zip"
    zip_path = server_dir / zip_name
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in pkg_root.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(server_dir))
    shutil.rmtree(pkg_root, ignore_errors=True)

    # 3. 生成模拟 GitHub API 响应
    size = zip_path.stat().st_size
    releases = [
        {
            "tag_name": f"v{version}",
            "name": f"Release {version}",
            "draft": False,
            "prerelease": False,
            "body": f"## 更新日志 {version}\n\n- 新增功能 A\n- 修复 bug B\n- 优化性能 C",
            "assets": [
                {
                    "name": zip_name,
                    "size": size,
                    "browser_download_url": f"http://127.0.0.1:{MOCK_PORT}/{zip_name}",
                }
            ],
        }
    ]
    (server_dir / "releases").write_text(
        json.dumps(releases, ensure_ascii=False), encoding="utf-8"
    )
    return zip_name, size


def main():
    server_dir = Path(tempfile.mkdtemp(prefix="app_demo_mock_"))
    print(f"[Test] 模拟服务器目录: {server_dir}")

    new_version = _bump_patch_version(CURRENT_VERSION)
    zip_name, size = build_fake_release(server_dir, new_version)
    print(f"[Test] 生成更新包: {zip_name} ({size} bytes)")

    # 启动本地 HTTP 服务器
    handler = partial(SimpleHTTPRequestHandler, directory=str(server_dir))
    httpd = HTTPServer(("127.0.0.1", MOCK_PORT), handler)
    # 用 /releases 返回 API JSON，/latest/download 也返回 API JSON
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    print(f"[Test] 模拟 GitHub 服务: http://127.0.0.1:{MOCK_PORT}")

    # 导入 updater（此时环境变量已生效）
    from backend.core.updater import updater, get_progress

    passed = True

    # ── 测试 1: 检查更新 ──
    print("\n[Test] === 检查更新 ===")
    result = updater.check_for_update()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["has_update"]:
        print("[Test] FAIL: 应检测到新版本")
        passed = False
    elif result["latest_version"] != new_version:
        print(f"[Test] FAIL: 最新版本应为 {new_version}")
        passed = False
    else:
        print("[Test] PASS: 检测到新版本", new_version)

    if not result.get("notes"):
        print("[Test] FAIL: 更新日志为空")
        passed = False
    else:
        print("[Test] PASS: 更新日志已获取")

    # ── 测试 2: 应用更新 ──
    print("\n[Test] === 应用更新 ===")
    # 使用临时目录作为"应用目录"，避免污染真实项目
    app_dir = Path(tempfile.mkdtemp(prefix="app_demo_target_"))
    updater.data_dir = app_dir / "pyu-data"
    updater.data_dir.mkdir(parents=True, exist_ok=True)
    updater._get_app_dir = lambda: app_dir  # 覆盖应用目录

    thread = updater.apply_update()
    if thread is None:
        print("[Test] FAIL: 更新线程未启动")
        passed = False
    else:
        thread.join(timeout=30)

    progress = get_progress()
    print("[Test] 最终进度:", json.dumps(progress, ensure_ascii=False))
    if progress["phase"] != "done":
        print(f"[Test] FAIL: 更新未完成，phase={progress['phase']}, error={progress.get('error')}")
        passed = False
    else:
        print("[Test] PASS: 更新完成")

    # ── 测试 3: 验证文件已替换 ──
    print("\n[Test] === 验证文件应用 ===")
    new_file = app_dir / "backend" / "new_feature.txt"
    if new_file.exists():
        print(f"[Test] PASS: 新文件已写入 -> {new_file}")
        print("       内容:", new_file.read_text(encoding="utf-8").strip())
    else:
        print("[Test] FAIL: 新文件未找到")
        passed = False

    # 清理
    httpd.shutdown()
    shutil.rmtree(server_dir, ignore_errors=True)
    shutil.rmtree(app_dir, ignore_errors=True)

    print("\n" + "=" * 50)
    print("[Test] 结果:", "全部通过" if passed else "存在失败")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
