# app_demo

Python + Vue 桌面应用，基于 **pywebview + FastAPI + Vue 3**，内置 **GitHub Releases 自动更新**功能。

## 技术栈

| 层 | 技术 |
|---|---|
| 桌面外壳 | pywebview（系统原生 WebView） |
| 后端 | FastAPI + uvicorn |
| 前端 | Vue 3 + Vite + TypeScript + Pinia + Element Plus |
| 更新日志渲染 | markdown-it + DOMPurify |
| 打包 | PyInstaller（onedir） |
| 更新源 | GitHub Releases（`lice-cloud/app_demo`） |

## 目录结构

```
app_demo/
├── backend/                  # Python 后端
│   ├── __init__.py           # 版本号 (__version__ = "0.1.0")
│   ├── main.py               # 入口：uvicorn + pywebview + 启动检查更新
│   ├── client_config.py      # PyUpdater 兼容配置（可选）
│   ├── api/v1/
│   │   ├── health.py         # GET /api/v1/health
│   │   └── update.py         # GET /check, /status; POST /apply, /restart
│   ├── core/
│   │   ├── config.py         # 应用配置、GITHUB_REPO
│   │   └── updater.py        # 自包含更新客户端（GitHub Releases）
│   └── web_dist/             # 前端构建产物（vite build 输出）
├── frontend/                 # Vue 3 前端
│   └── src/
│       ├── api/              # axios 封装 + 接口
│       ├── components/       # UpdateDialog.vue（Markdown 富文本）
│       ├── stores/           # Pinia（update store）
│       └── views/Settings/   # Update.vue
├── build/
│   └── pyinstaller.spec      # 打包配置（onedir）
└── scripts/
    ├── dev.ps1 / dev.sh      # 开发一键启动
    └── test_update_flow.py   # 本地更新闭环测试
```

## 开发

### 1. 安装依赖

```bash
# 后端
cd backend
pip install fastapi uvicorn pywebview

# 前端
cd frontend
npm install
```

### 2. 启动（开发模式）

Windows:
```powershell
.\scripts\dev.ps1
```

Linux / macOS:
```bash
./scripts/dev.sh
```

脚本会同时启动 Vite dev server（HMR）与后端（`--dev` 模式加载 `http://127.0.0.1:5173`）。

### 3. 构建前端

```bash
cd frontend
npm run build      # 输出到 backend/web_dist
```

之后直接运行后端即可加载生产静态资源：

```bash
python backend/main.py
```

## 更新功能

- **触发时机**：应用启动后延迟 3 秒自动检查；也可在「软件更新」页手动检查
- **更新来源**：GitHub Releases API（`https://api.github.com/repos/lice-cloud/app_demo/releases`）
- **更新范围**：全量更新（zip / tar.gz）
- **交互**：发现新版本 → 弹窗展示 Markdown 更新日志 → 用户确认后下载安装 → 提示重启
- **平台**：Windows（`win-x64`）+ Linux（`linux-x64`）

### 更新执行流程（onedir）

1. **检查**：读取 GitHub Releases，取最新非草稿/非预发布版本，与本地版本比较
2. **下载 + 暂存**：按平台关键词（`win-x64` / `linux-x64`）选择资产，下载 → 解压 → 归一化顶层目录 → 复制到用户数据目录 `.../app_demo/updater/staging`
3. **重启应用**：写入 `pending_update.json` 标记，用户点击重启后启动一个**独立辅助进程**（Windows 为 `apply_update.cmd`，Linux 为 `apply_update.sh`）：
   - 辅助进程等待主进程退出（Windows 用 `tasklist` 轮询 PID）
   - `robocopy`/`cp` 覆盖安装目录（此时文件锁已释放，可替换 exe 与 `_internal` 下的 DLL）
   - 重新拉起应用
4. **启动核对**：新版本启动时 `reconcile_pending_on_startup()` 比较版本号，确认更新已生效后清理暂存与标记

> 关键点：**不能**在应用运行时直接覆盖 `app_demo.exe` 和 `_internal/*.dll`（被进程占用），因此采用「退出后由辅助进程替换」策略。Windows 辅助进程使用 `CREATE_NO_WINDOW`（不可用 `DETACHED_PROCESS`，否则 `tasklist`/`find` 等无法执行）。

用户在界面点击「重启以完成更新」→ 调用 `POST /api/v1/update/restart`。

### 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/update/check` | 检查更新，返回版本、更新日志 |
| GET | `/api/v1/update/status` | 更新进度（phase/percent/bytes） |
| POST | `/api/v1/update/apply` | 开始下载并暂存/应用更新 |
| GET | `/api/v1/update/pending` | 是否有已暂存、等待重启的更新 |
| POST | `/api/v1/update/restart` | 应用暂存更新并重启应用 |

进度 `phase` 取值：`idle` → `checking` → `downloading` → `verifying` → `installing` → `ready`（冻结环境，等待重启）/ `done`（开发环境，已即时替换）/ `error`。

### 本地测试更新闭环

无需真实 GitHub Release，运行：

```bash
python scripts/test_update_flow.py
```

该脚本会启动本地模拟 GitHub 服务，生成假更新包并验证「检查 → 下载 → 校验 → 应用」全流程。

### 发布新版本

**方式一：GitHub Actions 自动发布（推荐）**

1. 修改 `backend/__init__.py` 中的 `__version__`（如 `0.1.0` → `0.1.1`）并提交
2. 打标签并推送：
   ```bash
   git tag v0.1.1
   git push origin master --tags
   ```
3. `.github/workflows/release.yml` 会自动：
   - 构建前端与 PyInstaller onedir 产物
   - 生成便携包 `app_demo-win-x64-0.1.1.zip`、`app_demo-linux-x64-0.1.1.tar.gz`
   - 用 Inno Setup 生成安装程序 `app_demo-setup-0.1.1.exe`
   - 创建 GitHub Release 并上传以上产物
4. 客户端启动时即可检测到 `0.1.1` 并通过 Release API 获取更新

**方式二：本地构建**

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_release.ps1
```

（需本地安装 Inno Setup 6 才会生成安装程序，否则仅生成便携 zip。）

> 更新资产命名需包含平台标识（`win-x64` / `linux-x64`），客户端按此选择对应包。

### Windows 安装程序（可选安装位置）

`build/installer.iss` 使用 Inno Setup 6 生成安装向导：

- **安装向导中可选择安装位置**（`DefaultDirName` 仅为默认值）
- `PrivilegesRequiredOverridesAllowed=dialog`：允许用户选择
  - 「仅为我安装」→ 默认 `%LOCALAPPDATA%\Programs\app_demo`，**免管理员**
  - 「为所有用户安装」→ 默认 `C:\Program Files\app_demo`，需管理员
- 选择免管理员（用户目录）时，**自动更新无需提权**即可替换文件

本地编译：

```powershell
iscc /DMyAppVersion=0.1.0 build\installer.iss
```

> 注意：若安装到 `C:\Program Files`，更新时需要管理员权限才能替换文件，
> 否则更新辅助进程会因权限不足失败。推荐使用默认的用户目录安装方式。

## CI/CD

- **CI**（`.github/workflows/ci.yml`）：push / PR 时运行后端导入检查、更新流程测试（本地模拟）与前端构建
- **Release**（`.github/workflows/release.yml`）：推送 `v*` 标签时构建 Windows / Linux 产物并发布 Release（含 Inno Setup 安装程序）

## 注意事项

- 仅监听 `127.0.0.1`，更新接口不对外暴露
- 采用 **onedir** 打包，便于文件替换式更新
- Windows 下运行中的 exe / DLL 无法被覆盖，更新在应用退出后由辅助进程完成替换并自动重启
- 更新包解压后会自动归一化顶层目录，因此压缩时既可包含顶层 `app_demo/` 目录，也可直接放置其内容
- 当前未启用数字签名；如需校验可在 `updater.py` 中扩展 SHA-256 校验
