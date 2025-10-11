"""
Supervisor Agent - 模型驱动的主管智能体
负责分析输入数据并制定最优执行策略
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

from .base_agent import BaseAgent
from .types import AgentStatus, StageResult, TaskSpec, AgentCapability
from ...utils.logging import get_logger

logger = get_logger(__name__)

# 系统提示词
SUPERVISOR_SYSTEM_PROMPT = """你是一个专业的生物信息学主管智能体，负责为线粒体基因组分析流水线制定最优策略。

你的职责：
1. 分析输入数据特征（读长类型、数据量、质量等）
2. 根据物种类型和数据特征选择最适合的工具链
3. 制定详细的执行计划和参数配置
4. 设置备用方案和容错策略

请严格按照 JSON 格式输出，不要包含任何其他文本。"""

# 用户提示词模板
SUPERVISOR_USER_PROMPT = """请为以下线粒体基因组分析任务制定执行策略：

## 输入数据信息
- 测序文件: {reads_file}
- 读长类型提示: {read_type_hint}
- 物种类型: {kingdom}
- 预估数据大小: {file_size}

## 约束条件
- 跳过质控: {skip_qc}
- 跳过注释: {skip_annotation}
- 生成报告: {generate_report}
- 最大线程数: {max_threads}
- 内存限制: {memory_limit}

## 可用工具
质控工具: FastQC, NanoPlot, Trimmomatic
组装工具: SPAdes, Flye, Unicycler, Hifiasm, Miniasm, Canu
注释工具: MITOS, GeSeq, CPGAVAS

请输出包含以下字段的 JSON：
{{
  "strategy": {{
    "name": "策略名称",
    "description": "策略描述"
  }},
  "tools": {{
    "qc": "质控工具名称或null",
    "trimming": "修剪工具名称或null", 
    "assembly": "组装工具名称",
    "polishing": "抛光工具名称或null",
    "annotation": "注释工具名称"
  }},
  "parameters": {{
    "工具名称": {{"参数名": "参数值"}},
    "...": "各工具的具体参数"
  }},
  "stages": ["阶段1", "阶段2", "..."],
  "fallbacks": {{
    "assembly": ["备用工具1", "备用工具2"],
    "annotation": ["备用工具1", "备用工具2"]
  }},
  "resource_requirements": {{
    "estimated_memory_gb": 数值,
    "estimated_time_minutes": 数值,
    "recommended_threads": 数值
  }},
  "quality_thresholds": {{
    "min_qc_score": 数值,
    "min_assembly_n50": 数值,
    "min_annotation_genes": 数值
  }},
  "reasoning": "选择此策略的详细理由",
  "confidence": 0.0到1.0之间的置信度
}}"""

class SupervisorAgent(BaseAgent):
    """模型驱动的 Supervisor Agent"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("supervisor", config)
        
        # Supervisor 特有的配置
        self.analysis_timeout = self.config.get("analysis_timeout", 300)  # 5分钟超时
        self.max_retries = self.config.get("max_retries", 3)
    
    def get_capability(self) -> AgentCapability:
        """返回 Supervisor Agent 的能力描述"""
        return AgentCapability(
            name="supervisor",
            description="AI-powered supervisor for mitochondrial genome analysis pipeline",
            supported_inputs=["reads", "kingdom", "read_type"],
            supported_outputs=["strategy", "execution_plan", "tool_selection"],
            resource_requirements={
                "cpu_cores": 1,
                "memory_gb": 2,
                "disk_gb": 1,
                "estimated_time_sec": 60
            },
            dependencies=[]
        )
    
    def prepare(self, workdir: Path, **kwargs) -> None:
        """准备阶段 - 设置工作目录和初始化"""
        self.workdir = workdir
        self.workdir.mkdir(parents=True, exist_ok=True)
        
        # 创建分析目录
        (self.workdir / "supervisor").mkdir(exist_ok=True)
        
        logger.info(f"Supervisor Agent prepared in {workdir}")
    
    def run(self, inputs: Dict[str, Any], **config) -> StageResult:
        """运行 Supervisor 分析"""
        return self.execute_stage(inputs)
    
    def finalize(self) -> None:
        """清理和后处理"""
        logger.info("Supervisor Agent finalized")
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """验证输入数据"""
        required_fields = ["reads"]
        for field in required_fields:
            if field not in inputs:
                logger.error(f"Missing required input field: {field}")
                return False
        
        # 检查读取文件是否存在
        reads_file = inputs.get("reads")
        if reads_file and not Path(reads_file).exists():
            logger.error(f"Reads file not found: {reads_file}")
            return False
        
        return True
    
    def execute_stage(self, inputs: Dict[str, Any]) -> StageResult:
        """执行 Supervisor 分析阶段"""
        self.status = AgentStatus.RUNNING
        self.emit_event("stage_start", stage="analysis")
        
        try:
            # 验证输入
            if not self.validate_inputs(inputs):
                raise ValueError("Input validation failed")
            
            # 执行分析
            strategy = self.analyze_and_plan(inputs)
            
            # 构建结果
            result = StageResult(
                status=AgentStatus.FINISHED,
                outputs={"strategy": strategy},
                metrics={"confidence": strategy.get("confidence", 0.7)},
                logs={"analysis": self.workdir / "supervisor_analysis.json" if self.workdir else Path("supervisor_analysis.json")}
            )
            
            self.status = AgentStatus.FINISHED
            self.emit_event("stage_complete", stage="analysis", success=True)
            
            return result
            
        except Exception as e:
            logger.error(f"Supervisor analysis failed: {e}")
            self.status = AgentStatus.FAILED
            self.emit_event("stage_complete", stage="analysis", success=False, error=str(e))
            
            return StageResult(
                status=AgentStatus.FAILED,
                outputs={},
                metrics={},
                logs={},
                errors=[str(e)]
            )
    
    def analyze_and_plan(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析输入数据并制定执行计划
        
        Args:
            inputs: 输入数据信息
            
        Returns:
            Dict[str, Any]: 执行计划
        """
        logger.info("🧠 Supervisor Agent starting analysis...")
        
        try:
            # 准备输入信息
            analysis_input = self._prepare_analysis_input(inputs)
            
            # 调用模型生成策略
            strategy = self._generate_strategy(analysis_input)
            
            # 验证和后处理策略
            validated_strategy = self._validate_strategy(strategy)
            
            # 保存分析结果
            if self.workdir:
                self._save_analysis_results(validated_strategy, self.workdir)
            
            logger.info(f"✅ Strategy selected: {validated_strategy['strategy']['name']}")
            logger.info(f"📊 Confidence: {validated_strategy['confidence']:.2f}")
            
            return validated_strategy
            
        except Exception as e:
            logger.error(f"❌ Supervisor analysis failed: {e}")
            
            # 使用默认策略作为备用
            logger.warning("🔧 Using default strategy as fallback")
            fallback = self._get_default_strategy(inputs)
            # 在默认策略中也注入引用，并写入记忆（引用为空）
            try:
                if isinstance(fallback, dict):
                    fallback.setdefault("references", [])
                    fallback["references"] = []
                self.memory_write({
                    "type": "supervisor_strategy_fallback",
                    "strategy_name": (fallback or {}).get("strategy", {}).get("name") if isinstance(fallback, dict) else "unknown",
                    "references": [],
                    "tags": ["supervisor"]
                })
            except Exception:
                pass
            return fallback
    
    def _prepare_analysis_input(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """准备分析输入数据"""
        reads_file = inputs.get("reads", "")
        
        # 获取文件大小
        file_size = "unknown"
        try:
            if isinstance(reads_file, str) and Path(reads_file).exists():
                size_bytes = Path(reads_file).stat().st_size
                file_size = f"{size_bytes / (1024**3):.2f} GB"
        except Exception:
            pass
        
        return {
            "reads_file": Path(reads_file).name if reads_file else "unknown",
            "read_type_hint": inputs.get("read_type", "unknown"),
            "kingdom": inputs.get("kingdom", "animal"),
            "file_size": file_size,
            "skip_qc": self.config.get("skip_qc", False),
            "skip_annotation": self.config.get("skip_annotation", False),
            "generate_report": self.config.get("generate_report", True),
            "max_threads": self.config.get("threads", 8),
            "memory_limit": self.config.get("memory", "16G")
        }
    
    def _generate_strategy(self, analysis_input: Dict[str, Any]) -> Dict[str, Any]:
        """调用模型生成策略"""
        # 构建提示词
        prompt = SUPERVISOR_USER_PROMPT.format(**analysis_input)
        # 记忆查询与RAG增强（自动探测，不可用则回退）
        try:
            tags = ["supervisor", analysis_input.get("read_type_hint", "unknown"), analysis_input.get("kingdom", "unknown")]
            _mem_items = self.memory_query(tags=tags, top_k=3)
        except Exception:
            _mem_items = []
        augmented_prompt, citations = self.rag_augment(prompt, task=None, top_k=4)
        
        # 定义 JSON Schema
        schema = {
            "type": "object",
            "required": ["strategy", "tools", "stages", "reasoning", "confidence"],
            "properties": {
                "strategy": {"type": "object"},
                "tools": {"type": "object"},
                "parameters": {"type": "object"},
                "stages": {"type": "array"},
                "fallbacks": {"type": "object"},
                "resource_requirements": {"type": "object"},
                "quality_thresholds": {"type": "object"},
                "reasoning": {"type": "string"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1}
            }
        }
        
        # 调用模型
        logger.debug("Calling model for strategy generation...")
        start_time = time.time()
        
        result = self.generate_llm_json(
            prompt=augmented_prompt,
            system=SUPERVISOR_SYSTEM_PROMPT,
            schema=schema,
            temperature=0.2,
            max_tokens=4000,
            max_retries=self.max_retries
        )
        
        elapsed_time = time.time() - start_time
        logger.debug(f"Model call completed in {elapsed_time:.2f}s")
        
        # 注入引用并写入记忆（静默失败）
        try:
            if isinstance(result, dict):
                result.setdefault("references", [])
                result["references"] = citations or []
            self.memory_write({
                "type": "supervisor_strategy",
                "strategy_name": (result or {}).get("strategy", {}).get("name") if isinstance(result, dict) else "unknown",
                "references": citations or [],
                "tags": ["supervisor"]
            })
        except Exception:
            pass

        return result
    
    def _validate_strategy(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """验证和后处理策略"""
        # 检查是否有错误
        if "error" in strategy:
            raise ValueError(f"Model returned error: {strategy['error']}")
        
        # 设置默认值
        validated = {
            "strategy": strategy.get("strategy", {"name": "Default", "description": "Default strategy"}),
            "tools": strategy.get("tools", {}),
            "parameters": strategy.get("parameters", {}),
            "stages": strategy.get("stages", ["qc", "assembly", "annotation", "report"]),
            "fallbacks": strategy.get("fallbacks", {}),
            "resource_requirements": strategy.get("resource_requirements", {}),
            "quality_thresholds": strategy.get("quality_thresholds", {}),
            "reasoning": strategy.get("reasoning", "Strategy generated by AI model"),
            "confidence": max(0.0, min(1.0, strategy.get("confidence", 0.7)))  # 确保在 0-1 范围内
        }
        
        # 验证必需的工具
        if not validated["tools"].get("assembly"):
            validated["tools"]["assembly"] = "spades"  # 默认组装工具
        
        if not validated["tools"].get("annotation"):
            validated["tools"]["annotation"] = "mitos"  # 默认注释工具
        
        # 确保阶段列表不为空
        if not validated["stages"]:
            validated["stages"] = ["qc", "assembly", "annotation", "report"]
        
        # 传递引用（如有）到验证后的策略
        try:
            validated["references"] = strategy.get("references", [])
        except Exception:
            validated["references"] = []
        
        return validated
    
    def _save_analysis_results(self, strategy: Dict[str, Any], workdir: Path) -> None:
        """保存分析结果到文件"""
        try:
            # 创建完整的分析报告
            analysis_report = {
                "supervisor_analysis": {
                    "timestamp": time.time(),
                    "model_info": self.get_llm_info(),
                    "strategy": strategy,
                    "version": "2.0.0"
                }
            }
            
            # 保存到 JSON 文件
            analysis_file = workdir / "supervisor_analysis.json"
            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_report, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Analysis results saved to {analysis_file}")
            
        except Exception as e:
            logger.warning(f"Failed to save analysis results: {e}")
    
    def _get_default_strategy(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """获取默认策略（当模型调用失败时使用）"""
        read_type = inputs.get("read_type", "illumina")
        kingdom = inputs.get("kingdom", "animal")
        
        # 基于规则的默认策略
        if read_type == "nanopore":
            assembly_tool = "flye"
        elif read_type == "pacbio_hifi":
            assembly_tool = "hifiasm"
        else:
            assembly_tool = "spades"
        
        annotation_tool = "mitos" if kingdom == "animal" else "geseq"
        
        return {
            "strategy": {
                "name": f"Default_{read_type.title()}_{kingdom.title()}",
                "description": f"Default strategy for {read_type} reads and {kingdom} species"
            },
            "tools": {
                "qc": "fastqc" if not self.config.get("skip_qc") else None,
                "assembly": assembly_tool,
                "annotation": annotation_tool if not self.config.get("skip_annotation") else None
            },
            "parameters": {
                assembly_tool: {"threads": self.config.get("threads", 8)},
                annotation_tool: {"genetic_code": 2 if kingdom == "animal" else 1}
            },
            "stages": ["qc", "assembly", "annotation", "report"],
            "fallbacks": {
                "assembly": ["unicycler", "miniasm"],
                "annotation": ["geseq", "cpgavas"]
            },
            "resource_requirements": {
                "estimated_memory_gb": 16,
                "estimated_time_minutes": 60,
                "recommended_threads": self.config.get("threads", 8)
            },
            "quality_thresholds": {
                "min_qc_score": 0.6,
                "min_assembly_n50": 10000,
                "min_annotation_genes": 10
            },
            "reasoning": "Default rule-based strategy used as fallback when AI model is unavailable",
            "confidence": 0.6
        }
    
    def analyze_error_from_log(self, log_path: Path, failed_stage: str) -> Dict[str, Any]:
        """
        从 pipeline.log 分析错误
        
        Args:
            log_path: pipeline.log 路径
            failed_stage: 失败的阶段（qc/assembly/annotation）
        
        Returns:
            错误诊断和修复建议
        """
        try:
            # 读取日志文件
            if not log_path.exists():
                logger.warning(f"Log file not found: {log_path}")
                return self._get_default_diagnosis(failed_stage)
            
            log_content = log_path.read_text(encoding='utf-8')
            
            # 提取最近的错误日志（最后 2000 字符）
            recent_log = log_content[-2000:] if len(log_content) > 2000 else log_content
            
            # 构建诊断提示词
            diagnosis_prompt = f"""分析以下 {failed_stage} 阶段的错误日志：

```
{recent_log}
```

请深入诊断：

1. **错误类型**（选择一个）：
   - tool_not_found: 工具未安装或不可用
   - parameter_error: 参数配置错误
   - input_quality: 输入数据质量问题
   - resource_limit: 系统资源不足（内存/磁盘/超时）
   - tool_bug: 工具本身的 bug 或版本问题
   - data_format: 数据格式不兼容
   - unknown: 无法确定

2. **根本原因**：简洁准确地说明问题所在

3. **是否可以重试**：基于错误类型判断

4. **推荐的修复动作**（选择一个）：
   - retry: 简单重试
   - switch_tool: 切换到其他工具
   - adjust_params: 调整参数后重试
   - abort: 无法自动修复，需要人工干预

5. **具体建议**：
   - 如果推荐切换工具，说明推荐哪个工具及原因
   - 如果推荐调整参数，给出具体参数名和值
   - 解释为什么这样做能解决问题

请严格按照以下 JSON 格式输出：
{{
  "error_type": "类型",
  "root_cause": "根本原因的简洁描述",
  "can_retry": true 或 false,
  "recommended_action": "retry/switch_tool/adjust_params/abort",
  "suggestions": {{
    "alternative_tool": "工具名或null",
    "parameter_adjustments": {{"参数名": "参数值"}},
    "explanation": "为什么这样做能解决问题"
  }}
}}"""
            
            # 调用 LLM 进行诊断
            logger.info(f"Supervisor analyzing error for {failed_stage} stage...")
            
            schema = {
                "type": "object",
                "properties": {
                    "error_type": {"type": "string"},
                    "root_cause": {"type": "string"},
                    "can_retry": {"type": "boolean"},
                    "recommended_action": {"type": "string"},
                    "suggestions": {
                        "type": "object",
                        "properties": {
                            "alternative_tool": {"type": ["string", "null"]},
                            "parameter_adjustments": {"type": "object"},
                            "explanation": {"type": "string"}
                        }
                    }
                },
                "required": ["error_type", "root_cause", "can_retry", "recommended_action"]
            }
            
            diagnosis = self.call_llm(
                diagnosis_prompt,
                schema=schema,
                temperature=0.3  # 降低温度以获得更确定的诊断
            )
            
            logger.info(
                f"✓ Error diagnosis complete: {diagnosis['error_type']} - "
                f"{diagnosis['root_cause']}"
            )
            
            return diagnosis
            
        except Exception as e:
            logger.warning(f"Error diagnosis failed: {e}, using default diagnosis")
            return self._get_default_diagnosis(failed_stage)
    
    def generate_recovery_strategy(self, 
                                   diagnosis: Dict[str, Any],
                                   current_strategy: Dict[str, Any],
                                   retry_count: int) -> Optional[Dict[str, Any]]:
        """
        根据错误诊断生成恢复策略
        
        Args:
            diagnosis: 错误诊断结果（来自 analyze_error_from_log）
            current_strategy: 当前执行策略
            retry_count: 当前重试次数
        
        Returns:
            新的执行策略，如果无法恢复则返回 None
        """
        try:
            action = diagnosis["recommended_action"]
            suggestions = diagnosis.get("suggestions", {})
            
            # 无法自动恢复
            if action == "abort":
                logger.error(
                    f"Cannot auto-recover: {diagnosis['root_cause']}"
                )
                return None
            
            # 超过最大重试次数
            if retry_count >= 2:
                logger.warning(
                    f"Max retries ({retry_count}) reached, cannot retry"
                )
                return None
            
            # 创建新策略（深拷贝避免修改原策略）
            new_strategy = json.loads(json.dumps(current_strategy))
            
            # 根据诊断建议修改策略
            if action == "switch_tool":
                alt_tool = suggestions.get("alternative_tool")
                if alt_tool:
                    stage = self._identify_failed_stage(diagnosis, current_strategy)
                    if stage:
                        old_tool = new_strategy["tools"].get(stage)
                        new_strategy["tools"][stage] = alt_tool
                        
                        logger.info(
                            f"🔧 Recovery: Switching {stage} tool from "
                            f"{old_tool} to {alt_tool}"
                        )
                        logger.info(f"   Reason: {suggestions.get('explanation', 'N/A')}")
                    else:
                        logger.warning("Cannot identify failed stage for tool switch")
                        return None
                else:
                    logger.warning("No alternative tool suggested")
                    return None
            
            elif action == "adjust_params":
                params = suggestions.get("parameter_adjustments", {})
                if params:
                    # 更新参数
                    if "parameters" not in new_strategy:
                        new_strategy["parameters"] = {}
                    
                    for key, value in params.items():
                        new_strategy["parameters"][key] = value
                    
                    logger.info(f"🔧 Recovery: Adjusting parameters: {params}")
                    logger.info(f"   Reason: {suggestions.get('explanation', 'N/A')}")
                else:
                    logger.warning("No parameter adjustments suggested")
                    # 简单重试
                    logger.info("🔧 Recovery: Retrying with same configuration")
            
            elif action == "retry":
                logger.info("🔧 Recovery: Retrying with same configuration")
                # 策略不变
            
            else:
                logger.warning(f"Unknown recovery action: {action}")
                return None
            
            return new_strategy
            
        except Exception as e:
            logger.error(f"Failed to generate recovery strategy: {e}")
            return None
    
    def _identify_failed_stage(self, diagnosis: Dict[str, Any],
                               current_strategy: Dict[str, Any]) -> Optional[str]:
        """
        根据错误诊断识别失败的阶段
        
        Args:
            diagnosis: 错误诊断
            current_strategy: 当前策略
        
        Returns:
            阶段名称（qc/assembly/annotation）或 None
        """
        # 从错误信息中推断阶段
        error_msg = diagnosis.get("root_cause", "").lower()
        
        # 关键词匹配
        if any(word in error_msg for word in ["assembly", "spades", "flye", "contig", "scaffold"]):
            return "assembly"
        elif any(word in error_msg for word in ["annotation", "mitos", "gene", "cds", "trna"]):
            return "annotation"
        elif any(word in error_msg for word in ["qc", "quality", "fastqc", "trimming"]):
            return "qc"
        
        # 如果无法从错误信息推断，尝试从当前工具推断
        tools = current_strategy.get("tools", {})
        error_type = diagnosis.get("error_type", "")
        
        if error_type == "tool_not_found":
            # 检查哪个工具不可用
            for stage, tool in tools.items():
                if tool and tool.lower() in error_msg:
                    return stage
        
        return None
    
    def _get_default_diagnosis(self, failed_stage: str) -> Dict[str, Any]:
        """获取默认的错误诊断（当 LLM 不可用时）"""
        return {
            "error_type": "unknown",
            "root_cause": f"{failed_stage} stage failed with unknown error",
            "can_retry": True,
            "recommended_action": "retry",
            "suggestions": {
                "alternative_tool": None,
                "parameter_adjustments": {},
                "explanation": "Simple retry without changes"
            }
        }