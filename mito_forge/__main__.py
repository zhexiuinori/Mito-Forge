"""
Mito-Forge 主入口点

支持 python -m mito_forge 调用
"""

import sys
from .cli.main import cli as main

if __name__ == "__main__":
    sys.exit(main())