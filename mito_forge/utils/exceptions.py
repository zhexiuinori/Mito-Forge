"""
异常处理模块

定义Mito-Forge的自定义异常类
"""

class MitoForgeError(Exception):
    """Mito-Forge基础异常类"""
    pass

class ConfigError(MitoForgeError):
    """配置相关错误"""
    pass

class ToolError(MitoForgeError):
    """生物信息学工具相关错误"""
    pass

class AgentError(MitoForgeError):
    """智能体相关错误"""
    pass

class PipelineError(MitoForgeError):
    """流水线执行错误"""
    pass

class KnowledgeBaseError(MitoForgeError):
    """知识库相关错误"""
    pass

class ValidationError(MitoForgeError):
    """数据验证错误"""
    pass

class FileError(MitoForgeError):
    """文件操作错误"""
    pass