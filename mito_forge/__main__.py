"""
Mito-Forge 主入口点

支持 python -m mito_forge 调用
"""

import sys
import os
# 为 Windows/GBK 环境统一设置标准输出/错误编码，避免子进程解码失败
# 仅在 Windows 环境下进行 GBK 重配置，其他平台跳过
try:
    if (getattr(sys, "platform", "").startswith("win")) or (os.name == "nt"):
        sys.stdout.reconfigure(encoding='gbk', errors='replace')
        sys.stderr.reconfigure(encoding='gbk', errors='replace')
except Exception:
    # 某些环境可能不支持 reconfigure，忽略以保持兼容
    pass
from .cli.main import cli as main

if __name__ == "__main__":
    sys.exit(main())