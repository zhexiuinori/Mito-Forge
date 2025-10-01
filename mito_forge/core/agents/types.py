"""
Agent 系统的核心类型定义
定义了 Agent 状态、执行结果、任务规格等标准化数据结构
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import time

class AgentStatus(Enum):
    """Agent 执行状态枚举"""
    IDLE = "idle"                    # 空闲状态
    PREPARING = "preparing"          # 准备阶段
    RUNNING = "running"              # 执行中
    FINISHED = "finished"            # 执行完成
    FAILED = "failed"                # 执行失败
    CANCELLED = "cancelled"          # 被取消

class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class AgentMetrics:
    """Agent 执行指标"""
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_sec: Optional[float] = None
    memory_peak_mb: Optional[float] = None
    cpu_percent: Optional[float] = None
    disk_usage_mb: Optional[float] = None
    
    def finish(self):
        """标记完成并计算耗时"""
        self.end_time = time.time()
        self.duration_sec = self.end_time - self.start_time

@dataclass
class StageResult:
    """标准化的阶段执行结果"""
    status: AgentStatus
    outputs: Dict[str, Any] = field(default_factory=dict)      # 输出文件路径、数据等
    metrics: Dict[str, Any] = field(default_factory=dict)      # 统计指标（N50、质量分数等）
    logs: Dict[str, Path] = field(default_factory=dict)        # 日志文件路径
    errors: List[str] = field(default_factory=list)           # 错误信息列表
    warnings: List[str] = field(default_factory=list)         # 警告信息列表
    agent_metrics: AgentMetrics = field(default_factory=AgentMetrics)
    
    # 扩展字段
    stage_name: str = ""
    agent_name: str = ""
    extra_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TaskSpec:
    """任务规格定义 - Supervisor 分配给 Agent 的任务"""
    task_id: str
    agent_type: str                                    # "qc", "assembly", "annotation" 等
    inputs: Dict[str, Any]                            # 输入数据（文件路径、参数等）
    config: Dict[str, Any] = field(default_factory=dict)  # 配置参数
    priority: TaskPriority = TaskPriority.NORMAL
    timeout_sec: Optional[int] = None
    retries: int = 0
    workdir: Optional[Path] = None
    
    # 工具选择与策略
    preferred_tools: List[str] = field(default_factory=list)  # ["flye", "spades"]
    fallback_tools: List[str] = field(default_factory=list)   # 备用工具
    execution_mode: str = "wrapper"                           # "wrapper" 或 "codegen"
    
    # 元数据
    created_at: float = field(default_factory=time.time)
    assigned_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentEvent:
    """Agent 事件 - 用于实时通信和监控"""
    event_type: str                    # "started", "progress", "log", "error", "finished"
    agent_name: str
    task_id: str
    timestamp: float = field(default_factory=time.time)
    payload: Dict[str, Any] = field(default_factory=dict)
    
    # 常用事件类型
    @classmethod
    def started(cls, agent_name: str, task_id: str, **kwargs):
        return cls("started", agent_name, task_id, payload=kwargs)
    
    @classmethod
    def progress(cls, agent_name: str, task_id: str, percent: float, message: str = "", **kwargs):
        return cls("progress", agent_name, task_id, payload={"percent": percent, "message": message, **kwargs})
    
    @classmethod
    def log(cls, agent_name: str, task_id: str, level: str, message: str, **kwargs):
        return cls("log", agent_name, task_id, payload={"level": level, "message": message, **kwargs})
    
    @classmethod
    def error(cls, agent_name: str, task_id: str, error: str, **kwargs):
        return cls("error", agent_name, task_id, payload={"error": error, **kwargs})
    
    @classmethod
    def finished(cls, agent_name: str, task_id: str, result: StageResult, **kwargs):
        return cls("finished", agent_name, task_id, payload={"result": result, **kwargs})

@dataclass
class AgentCapability:
    """Agent 能力描述"""
    name: str
    supported_inputs: List[str]        # 支持的输入类型 ["fastq", "fasta", "paired_reads"]
    supported_outputs: List[str]       # 输出类型 ["contigs", "annotations", "qc_report"]
    required_tools: List[str]          # 必需的外部工具
    optional_tools: List[str] = field(default_factory=list)
    resource_requirements: Dict[str, Any] = field(default_factory=dict)  # CPU、内存、磁盘需求
    estimated_runtime: Optional[str] = None  # 预估运行时间描述