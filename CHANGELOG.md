# 更新日志

应用内「软件更新」弹窗展示的更新说明，来自本文件（由发布工作流 `body_path: CHANGELOG.md` 注入到 GitHub Release body）。

发布新版本时，请在本文件顶部新增对应版本的条目。

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
