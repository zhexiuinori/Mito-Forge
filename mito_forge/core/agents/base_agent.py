"""
Agent 基类定义
所有具体 Agent（QC、Assembly、Annotation 等）的基础接口
"""
import abc
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List

from .types import AgentStatus, StageResult, TaskSpec, AgentEvent, AgentCapability, AgentMetrics
from ...utils.logging import get_logger

# 延迟导入 LLM 相关模块，避免启动时依赖检查
def _get_model_config_manager():
    """延迟导入 ModelConfigManager"""
    try:
        from ..llm.config_manager import ModelConfigManager
        return ModelConfigManager
    except ImportError as e:
        logger.warning(f"LLM 功能不可用: {e}")
        return None

def _get_model_provider():
    """延迟导入 ModelProvider"""
    try:
        from ..llm.provider import ModelProvider
        return ModelProvider
    except ImportError as e:
        logger.warning(f"LLM 提供者不可用: {e}")
        return None

logger = get_logger(__name__)

class BaseAgent(abc.ABC):
    """
    Agent 基类 - 定义统一的生命周期和接口
    
    所有 Agent 必须实现：
    1. prepare() - 准备阶段（检查工具、创建目录等）
    2. run() - 核心执行逻辑
    3. finalize() - 清理和后处理
    4. get_capability() - 返回能力描述
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.status = AgentStatus.IDLE
        self.current_task: Optional[TaskSpec] = None
        self.metrics = AgentMetrics()
        
        # 事件回调 - 用于向 Supervisor 或 CLI 报告状态
        self.event_callback: Optional[Callable[[AgentEvent], None]] = None
        
        # 工作目录和日志
        self.workdir: Optional[Path] = None
        self.logs_dir: Optional[Path] = None
        
        # LLM 提供者 - 延迟初始化
        self._provider: Optional[ModelProvider] = None
        self._profile_name: Optional[str] = config.get("llm_profile") if config else None
    
    def set_event_callback(self, callback: Callable[[AgentEvent], None]):
        """设置事件回调函数"""
        self.event_callback = callback
    
    def emit_event(self, event_type: str, **payload):
        """发送事件到上层（Supervisor/CLI）"""
        if self.event_callback and self.current_task:
            event = AgentEvent(
                event_type=event_type,
                agent_name=self.name,
                task_id=self.current_task.task_id,
                payload=payload
            )
            self.event_callback(event)
    
    def execute_task(self, task: TaskSpec) -> StageResult:
        """
        执行完整任务流程 - 外部调用的主入口
        包含完整的生命周期管理和异常处理
        """
        self.current_task = task
        self.status = AgentStatus.PREPARING
        self.metrics = AgentMetrics()
        
        try:
            # 发送开始事件
            self.emit_event("started", task_spec=task)
            
            # 准备阶段
            self.prepare(task.workdir or Path("work") / task.task_id, **task.inputs)
            
            # 执行阶段
            self.status = AgentStatus.RUNNING
            result = self.run(task.inputs, **task.config)
            
            # 完成阶段
            self.finalize()
            self.status = AgentStatus.FINISHED
            self.metrics.finish()
            
            # 填充结果元数据
            result.agent_name = self.name
            result.stage_name = task.agent_type
            result.agent_metrics = self.metrics
            
            # 发送完成事件
            self.emit_event("finished", result=result)
            
            return result
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            self.metrics.finish()
            
            # 创建失败结果
            error_result = StageResult(
                status=AgentStatus.FAILED,
                errors=[str(e)],
                agent_name=self.name,
                stage_name=task.agent_type if task else "unknown",
                agent_metrics=self.metrics
            )
            
            # 发送错误事件
            self.emit_event("error", error=str(e), result=error_result)
            
            return error_result
        
        finally:
            self.current_task = None
    
    @abc.abstractmethod
    def prepare(self, workdir: Path, **kwargs) -> None:
        """
        准备阶段 - 在执行前的初始化工作
        
        Args:
            workdir: 工作目录
            **kwargs: 任务输入参数
            
        应该包含：
        - 检查必需的工具是否可用
        - 创建工作目录结构
        - 验证输入文件
        - 设置日志路径
        """
        pass
    
    @abc.abstractmethod
    def run(self, inputs: Dict[str, Any], **config) -> StageResult:
        """
        核心执行逻辑
        
        Args:
            inputs: 输入数据字典
            **config: 配置参数
            
        Returns:
            StageResult: 标准化执行结果
            
        应该包含：
        - 调用外部工具或执行算法
        - 实时报告进度（通过 emit_event）
        - 解析工具输出
        - 生成统计指标
        """
        pass
    
    @abc.abstractmethod
    def finalize(self) -> None:
        """
        清理和后处理阶段
        
        应该包含：
        - 清理临时文件
        - 移动结果文件到最终位置
        - 生成摘要报告
        - 释放资源
        """
        pass
    
    @abc.abstractmethod
    def get_capability(self) -> AgentCapability:
        """
        返回 Agent 能力描述
        用于 Supervisor 进行任务分配决策
        """
        pass
    
    def get_status(self) -> AgentStatus:
        """获取当前状态"""
        return self.status
    
    def cancel(self) -> bool:
        """
        取消当前执行（如果支持）
        
        Returns:
            bool: 是否成功取消
        """
        if self.status in (AgentStatus.RUNNING, AgentStatus.PREPARING):
            self.status = AgentStatus.CANCELLED
            self.emit_event("cancelled")
            return True
        return False
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> List[str]:
        """
        验证输入参数
        
        Returns:
            List[str]: 错误信息列表，空列表表示验证通过
        """
        errors = []
        capability = self.get_capability()
        
        # 检查必需的输入类型
        for input_type in capability.supported_inputs:
            if input_type not in inputs:
                errors.append(f"Missing required input: {input_type}")
        
        return errors
    
    def estimate_resources(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        估算资源需求
        
        Returns:
            Dict: 包含 cpu_cores, memory_gb, disk_gb, estimated_time_sec 等
        """
        capability = self.get_capability()
        return capability.resource_requirements.copy()
    
    # ========== LLM 提供者相关方法 ==========
    
    def get_llm_provider(self):
        """
        获取 LLM 提供者实例（延迟初始化）
        
        Returns:
            ModelProvider: 统一的模型提供者，如果不可用则返回 None
        """
        if self._provider is None:
            try:
                ModelConfigManager = _get_model_config_manager()
                if ModelConfigManager is None:
                    logger.warning(f"Agent {self.name}: LLM 功能不可用，ModelConfigManager 导入失败")
                    return None
                
                config_manager = ModelConfigManager()
                if self._profile_name:
                    self._provider = config_manager.create_provider(self._profile_name)
                    logger.info(f"Agent {self.name} using LLM profile: {self._profile_name}")
                else:
                    self._provider = config_manager.create_provider_with_fallback()
                    logger.info(f"Agent {self.name} using default LLM provider with fallback")
            except Exception as e:
                logger.warning(f"Agent {self.name} LLM provider 初始化失败: {e}")
                logger.info(f"Agent {self.name} 将在无 LLM 模式下运行")
                return None
        
        return self._provider
    
    def generate_llm_response(
        self, 
        prompt: str, 
        *, 
        system: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        生成 LLM 文本响应的便捷方法
        
        Args:
            prompt: 用户提示词
            system: 系统提示词
            **kwargs: 其他参数（temperature, max_tokens 等）
            
        Returns:
            str: LLM 生成的文本，如果 LLM 不可用则返回默认响应
        """
        provider = self.get_llm_provider()
        
        if provider is None:
            # LLM 不可用时的降级处理
            logger.warning(f"Agent {self.name}: LLM 不可用，返回默认响应")
            return f"[LLM不可用] 基于规则的分析结果 - 提示词: {prompt[:100]}..."
        
        # 记录 LLM 调用
        self.emit_event("llm_call", prompt_length=len(prompt), system_length=len(system or ""))
        
        try:
            response = provider.generate(prompt, system=system, **kwargs)
            logger.debug(f"Agent {self.name} LLM response length: {len(response)}")
            return response
        except Exception as e:
            logger.error(f"Agent {self.name} LLM generation failed: {e}")
            self.emit_event("llm_error", error=str(e))
            # 降级处理而不是抛出异常
            return f"[LLM错误] 无法生成响应: {str(e)}"
    
    def generate_llm_json(
        self, 
        prompt: str, 
        *, 
        system: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成结构化 JSON 响应的便捷方法
        
        Args:
            prompt: 用户提示词
            system: 系统提示词
            schema: JSON Schema 约束
            max_retries: 最大重试次数
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 解析后的 JSON 对象
        """
        provider = self.get_llm_provider()
        
        # 记录 LLM 调用
        self.emit_event("llm_json_call", 
                       prompt_length=len(prompt), 
                       system_length=len(system or ""),
                       has_schema=schema is not None)
        
        try:
            response = provider.generate_json(
                prompt, 
                system=system, 
                schema=schema, 
                max_retries=max_retries, 
                **kwargs
            )
            logger.debug(f"Agent {self.name} LLM JSON response keys: {list(response.keys())}")
            return response
        except Exception as e:
            logger.error(f"Agent {self.name} LLM JSON generation failed: {e}")
            self.emit_event("llm_json_error", error=str(e))
            raise
    
    def get_llm_info(self) -> Dict[str, Any]:
        """
        获取当前 LLM 提供者信息
        
        Returns:
            Dict: 提供者信息
        """
        try:
            provider = self.get_llm_provider()
            return provider.get_model_info()
        except Exception as e:
            return {"error": str(e), "available": False}