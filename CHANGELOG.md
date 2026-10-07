# 更新日志

应用内「软件更新」弹窗展示的更新说明，来自本文件（由发布工作流 `body_path: CHANGELOG.md` 注入到 GitHub Release body）。

发布新版本时，请在本文件顶部新增对应版本的条目。

## v0.1.127
- 修复运行时任务栏图标仍不生效：之前的 Win32 兜底依赖 pywebview 已移除的 `_native_window` 属性（导致 WM_SETICON 从未执行）；改为直接枚举当前进程顶层窗口设置图标，并额外设置窗口类图标

## v0.1.126
- 修复任务栏图标仍显示默认图标：将原 `build/icon.ico` 畸形（256×246 非正方形）重做为合法正方形多尺寸 ICO，并修正运行时 Win32 图标设置的类型声明作为兜底

## v0.1.125
- 修复 Windows 任务栏图标仍显示默认 WinForms 图标的问题：改为使用 pywebview 原生的 `webview.start(icon=...)` 设置 `Form.Icon`

## v0.1.124
- 修复 Windows 任务栏/窗口图标不生效的问题：运行时通过 Win32 将应用图标（`build/icon.ico`）设到窗口，并将图标打包进运行时目录

## v0.1.123
- 补充前端 favicon（`frontend/public/favicon.ico`），修复 `index.html` 引用 `./favicon.ico` 产生的 404

## v0.1.122
- 修复健康检查接口 `/api/v1/health` 因误删 `import sys` 导致 500、前端提示“无法连接后端服务”的问题

## v0.1.121
- 修复打包版（onedir）缺失 `api/v1/settings` 模块导致启动时 500 的问题（已加入 PyInstaller 隐藏导入）
- 补全 settings 业务模块缺失的路由定义（`GET /api/v1/settings`）
- 增强启动健壮性：入口增加异常兜底与关键步骤日志，便于定位打包运行问题

## v0.1.12
- 重构后端路由聚合层（`api/v1` 集中注册），提升可扩展性
- 清理各模块中冗余的 `sys.path` 注入
- 新增示例业务模块 `api/v1/settings`（`GET /api/v1/settings`）
- 更新应用图标
- 修复更新测试脚本模拟版本低于当前版本导致 CI 失败的问题

## v0.1.11
- 修复更新对话框卡在“正在更新”的问题（未正确识别后端 `ready` 状态）

## v0.1.0
- 初始版本：pywebview + FastAPI + Vue 3 桌面应用，内置 GitHub Releases 自动更新
