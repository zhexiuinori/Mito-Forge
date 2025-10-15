"""
总指挥智能体

协调和管理所有专业智能体的工作，基于新的 Agent 架构
"""

from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import logging
from datetime import datetime

from .base_agent import BaseAgent
from .supervisor_agent import SupervisorAgent
from .qc_agent import QCAgent
from .assembly_agent import AssemblyAgent
from .annotation_agent import AnnotationAgent
from .types import StageResult, AgentStatus, AgentCapability

logger = logging.getLogger(__name__)


class Orchestrator(BaseAgent):
    """总指挥智能体类 - 协调整个分析流程"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化总指挥智能体
        
        Args:
            config: 配置参数，支持 llm_profile 等
        """
        super().__init__("orchestrator", config)
        self.description = "协调整个线粒体基因组分析流程"
        
        # 初始化专业智能体
        self.agents = {
            "supervisor": SupervisorAgent(config),
            "qc": QCAgent(config),
            "assembly": AssemblyAgent(config),
            "annotation": AnnotationAgent(config)
        }
        
        # 流水线状态
        self.pipeline_status = "idle"
        self.current_stage = None
        self.start_time = None
        self.end_time = None
    
    def prepare(self, workdir: Path, **kwargs) -> None:
        """准备阶段 - 设置工作目录和初始化资源"""
        self.workdir = workdir
        self.logs_dir = workdir / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化所有子Agent的工作目录
        for agent_name, agent in self.agents.items():
            agent_workdir = workdir / agent_name
            agent_workdir.mkdir(parents=True, exist_ok=True)
            agent.workdir = agent_workdir
    
    def run(self, inputs: Dict[str, Any], **config) -> StageResult:
        """核心执行逻辑 - 协调整个分析流水线"""
        return self.execute_stage(inputs)
    
    def finalize(self) -> None:
        """清理阶段 - 释放资源并生成最终报告"""
        # 清理临时资源
        self.pipeline_status = "idle"
        self.current_stage = None
        self.start_time = None
        self.end_time = None
    
    def get_capability(self) -> AgentCapability:
        """返回Orchestrator的能力描述"""
        return AgentCapability(
            name="orchestrator",
            supported_inputs=["reads", "read_type", "kingdom", "workdir"],
            supported_outputs=["pipeline_result", "stage_results", "summary"],
            required_tools=[],
            resource_requirements={
                "cpu_cores": 4,
                "memory_gb": 8,
                "disk_gb": 20,
                "estimated_runtime_sec": 3600
            },
            estimated_runtime="1小时（取决于数据大小和复杂度）"
        )
        
    def execute_stage(self, inputs: Dict[str, Any]) -> StageResult:
        """
        执行总指挥智能体的分析阶段
        
        Args:
            inputs: 输入数据
            
        Returns:
            StageResult: 执行结果
        """
        self.emit_event("start", message="开始总指挥分析")
        
        try:
            # 验证输入
            if not self._validate_inputs(inputs):
                return StageResult(
                    status=AgentStatus.FAILED,
                    errors=["输入数据验证失败"],
                    metrics={}
                )
            
            # 设置工作目录
            if "workdir" in inputs:
                self.workdir = Path(inputs["workdir"])
            
            # 执行完整的流水线
            pipeline_result = self._execute_pipeline(inputs)
            
            self.emit_event("complete", message="总指挥分析完成")
            return StageResult(
                status=AgentStatus.FINISHED,
                outputs={"pipeline_result": pipeline_result},
                metrics={
                    "total_stages": len(self.agents),
                    "execution_time": self._get_execution_time(),
                    "success_rate": self._calculate_success_rate(pipeline_result)
                }
            )
            
        except Exception as e:
            self.emit_event("error", message=f"总指挥分析失败: {e}")
            return StageResult(
                status=AgentStatus.FAILED,
                errors=[str(e)],
                metrics={}
            )
    
    def _execute_pipeline(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """执行完整的分析流水线"""
        logger.info("🚀 开始执行线粒体基因组分析流水线")
        self.pipeline_status = "running"
        self.start_time = datetime.now()
        
        pipeline_results = {}
        current_inputs = inputs.copy()
        
        # 按顺序执行各个阶段
        stages = ["supervisor", "qc", "assembly", "annotation"]
        
        for stage_name in stages:
            self.current_stage = stage_name
            logger.info(f"📋 执行阶段: {stage_name}")
            
            try:
                agent = self.agents[stage_name]
                agent.workdir = self.workdir
                
                # 执行当前阶段
                result = agent.execute_stage(current_inputs)
                
                if result.status == AgentStatus.FINISHED:
                    # 收集结果并传递给下一阶段
                    pipeline_results[stage_name] = result.outputs
                    current_inputs.update(result.outputs)
                    logger.info(f"✅ {stage_name} 阶段完成")
                else:
                    # 阶段失败，停止流水线
                    pipeline_results[stage_name] = {
                        "status": "failed",
                        "error": result.error
                    }
                    logger.error(f"❌ {stage_name} 阶段失败: {result.error}")
                    break
                    
            except Exception as e:
                pipeline_results[stage_name] = {
                    "status": "error",
                    "error": str(e)
                }
                logger.error(f"❌ {stage_name} 阶段异常: {e}")
                break
        
        self.pipeline_status = "completed" if all(
            stage_result.get("status") in ["completed", "finished"] 
            for stage_result in pipeline_results.values()
        ) else "failed"
        
        self.end_time = datetime.now()
        
        return {
            "pipeline_status": self.pipeline_status,
            "stage_results": pipeline_results,
            "execution_time": self._get_execution_time(),
            "summary": self._generate_summary(pipeline_results)
        }
    
    def _validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """验证输入数据"""
        required_fields = ["reads", "read_type", "kingdom"]
        
        for field in required_fields:
            if field not in inputs:
                logger.error(f"缺少必要输入字段: {field}")
                return False
        
        # 验证文件存在性
        if "reads" in inputs:
            reads_path = Path(inputs["reads"])
            if not reads_path.exists():
                logger.error(f"输入文件不存在: {reads_path}")
                return False
        
        return True
    
    def _get_execution_time(self) -> str:
        """计算执行时间"""
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            return str(duration)
        return "N/A"
    
    def _calculate_success_rate(self, pipeline_result: Dict[str, Any]) -> float:
        """计算成功率"""
        completed_stages = [
            stage for stage, result in pipeline_result.get("stage_results", {}).items()
            if result.get("status") in ["completed", "finished"]
        ]
        return len(completed_stages) / len(self.agents) if self.agents else 0.0
    
    def _generate_summary(self, pipeline_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成分析摘要"""
        summary = {
            "total_stages": len(pipeline_results),
            "completed_stages": sum(
                1 for result in pipeline_results.values() 
                if result.get("status") in ["completed", "finished"]
            ),
            "quality_scores": {},
            "recommendations": []
        }
        
        # 收集各阶段的质量评分
        for stage_name, result in pipeline_results.items():
            if "quality_score" in result:
                summary["quality_scores"][stage_name] = result["quality_score"]
        
        return summary
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """获取流水线状态"""
        return {
            "pipeline_status": self.pipeline_status,
            "current_stage": self.current_stage,
            "start_time": str(self.start_time) if self.start_time else "N/A",
            "end_time": str(self.end_time) if self.end_time else "N/A",
            "agents": list(self.agents.keys())
        }
    
    def get_agents_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有智能体的状态信息"""
        agents_status = {}
        
        for agent_name, agent in self.agents.items():
            # 模拟智能体状态信息
            agents_status[agent_name] = {
                "status": "active" if hasattr(agent, 'workdir') else "idle",
                "type": agent.__class__.__name__,
                "task_count": 0,  # 可以根据实际情况获取
                "memory_usage": 0.0,  # 可以根据实际情况获取
                "last_activity": "N/A"
            }
        
        return agents_status
    
    def restart_agent(self, agent_name: str) -> bool:
        """重启指定的智能体"""
        if agent_name not in self.agents:
            logger.error(f"智能体 {agent_name} 不存在")
            return False
        
        try:
            # 重新初始化智能体
            agent_class = self.agents[agent_name].__class__
            self.agents[agent_name] = agent_class(self.config)
            logger.info(f"智能体 {agent_name} 重启成功")
            return True
        except Exception as e:
            logger.error(f"重启智能体 {agent_name} 失败: {e}")
            return False