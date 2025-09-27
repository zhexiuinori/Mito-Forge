"""
Mito-Forge: 线粒体基因组学多智能体自动化框架

一个基于联邦知识系统的专业生物信息学分析工具
"""

__version__ = "1.0.0"
__author__ = "Mito-Forge Team"
__email__ = "contact@mito-forge.org"
__description__ = "线粒体基因组学多智能体自动化框架"

from .core.agents.orchestrator import Orchestrator
from .core.pipeline.manager import PipelineManager
from .utils.config import Config
from .utils.logging import setup_logging

# 设置默认日志
setup_logging()

# 导出主要类
__all__ = [
    "Orchestrator",
    "PipelineManager", 
    "Config",
    "__version__"
]