# PyUpdater 兼容配置（可选）
#
# 当前项目的更新客户端使用 backend/core/updater.py 中的自包含实现，
# 直接对接 GitHub Releases API，无需 PyUpdater 运行时依赖。
#
# 若后续希望切换到 PyUpdater 原生客户端，可保留本文件并提供以下字段：
#
#   class ClientConfig:
#       PUBLIC_KEY = None                      # 不启用签名
#       APP_NAME = "app_demo"
#       COMPANY_NAME = "lice-cloud"
#       UPDATE_URLS = [
#           "https://github.com/lice-cloud/app_demo/releases/latest/download/"
#       ]
#       MAX_DOWNLOAD_RETRIES = 3
#       HTTP_TIMEOUT = 30
#       DATA_DIR = "pyu-data"

try:
    from backend.core.config import APP_NAME, COMPANY_NAME, UPDATE_URLS
except Exception:
    APP_NAME = "app_demo"
    COMPANY_NAME = "lice-cloud"
    UPDATE_URLS = [
        "https://github.com/lice-cloud/app_demo/releases/latest/download/"
    ]


class ClientConfig:
    PUBLIC_KEY = None
    APP_NAME = APP_NAME
    COMPANY_NAME = COMPANY_NAME
    UPDATE_URLS = UPDATE_URLS
    MAX_DOWNLOAD_RETRIES = 3
    HTTP_TIMEOUT = 30
    DATA_DIR = "pyu-data"