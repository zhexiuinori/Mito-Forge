"""
Mito-Forge: 线粒体基因组学多智能体自动化框架

一个基于联邦知识系统的专业生物信息学分析工具
"""

__version__ = "1.0.0"
__author__ = "Mito-Forge Team"
__email__ = "contact@mito-forge.org"
__description__ = "线粒体基因组学多智能体自动化框架"

# 延迟导入，避免循环依赖和启动时加载所有模块
def get_orchestrator():
    """延迟导入 Orchestrator"""
    from .core.agents.orchestrator import Orchestrator
    return Orchestrator

def get_pipeline_manager():
    """延迟导入 PipelineManager"""
    from .core.pipeline.manager import PipelineManager
    return PipelineManager

def get_config():
    """延迟导入 Config"""
    from .utils.config import Config
    return Config

# 设置默认日志（轻量级操作）
try:
    from .utils.logging import setup_logging
    setup_logging()
except ImportError:
    # 如果日志模块有问题，使用标准日志
    import logging
    logging.basicConfig(level=logging.INFO)

# 导出主要接口
__all__ = [
    "get_orchestrator",
    "get_pipeline_manager", 
    "get_config",
    "__version__"
]