"""Agent执行异常定义"""


class AgentExecutionError(Exception):
    """Agent执行基础异常"""
    pass


class AssemblyFailedError(AgentExecutionError):
    """组装失败异常"""
    pass


class QCFailedError(AgentExecutionError):
    """质量控制失败异常"""
    pass


class AnnotationFailedError(AgentExecutionError):
    """基因注释失败异常"""
    pass


class ToolNotFoundError(AgentExecutionError):
    """工具未找到异常"""
    pass


class PipelinePausedException(AgentExecutionError):
    """Pipeline暂停异常(需要人工介入)"""
    def __init__(self, task_id: str, message: str):
        self.task_id = task_id
        super().__init__(message)
