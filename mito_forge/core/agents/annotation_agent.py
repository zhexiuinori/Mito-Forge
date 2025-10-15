"""
注释智能体 - 基于 AI 的基因注释分析
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from .base_agent import BaseAgent
from .types import AgentStatus, StageResult, AgentCapability
from .exceptions import AnnotationFailedError, ToolNotFoundError
from ...utils.logging import get_logger

logger = get_logger(__name__)

# 注释分析系统提示词
ANNOTATION_SYSTEM_PROMPT = """你是一个专业的生物信息学基因注释专家，负责分析基因注释结果并提供质量评估。

你的职责：
1. 评估注释完整性和准确性（基因数量、类型、功能等）
2. 识别注释问题（缺失基因、错误预测、重叠等）
3. 推荐注释优化策略和手动校正建议
4. 评估注释结果的生物学合理性

请严格按照 JSON 格式输出，不要包含任何其他文本。"""

# 注释分析提示词模板
ANNOTATION_ANALYSIS_PROMPT = """请分析以下基因注释结果：

## 注释基本信息
- 注释工具: {annotator}
- 基因组长度: {genome_length} bp
- 物种类型: {kingdom}
- 遗传密码: {genetic_code}

## 注释统计
- 总基因数: {total_genes}
- 蛋白编码基因: {protein_genes}
- tRNA基因: {trna_genes}
- rRNA基因: {rrna_genes}
- 其他基因: {other_genes}

## 基因覆盖
- 编码区覆盖率: {coding_coverage}%
- 基因组利用率: {genome_utilization}%
- 平均基因长度: {avg_gene_length} bp

## 预期标准（线粒体基因组）
- 预期蛋白编码基因: 13个
- 预期tRNA基因: 22个
- 预期rRNA基因: 2个
- 预期总基因数: 37个

## 检测到的问题
{detected_issues}

请输出包含以下字段的 JSON：
{{
  "annotation_quality": {{
    "overall_score": 0.0到1.0之间的总体质量评分,
    "grade": "A/B/C/D/F等级评定",
    "summary": "注释质量总结"
  }},
  "completeness_analysis": {{
    "protein_genes_complete": true/false,
    "trna_genes_complete": true/false,
    "rrna_genes_complete": true/false,
    "missing_genes": ["缺失基因列表"],
    "extra_genes": ["额外基因列表"],
    "completeness_percentage": 百分比数值
  }},
  "quality_issues": [
    {{
      "type": "问题类型",
      "severity": "low/medium/high/critical",
      "description": "问题描述",
      "affected_genes": ["影响的基因"],
      "suggestion": "修复建议"
    }}
  ],
  "functional_analysis": {{
    "essential_pathways_covered": true/false,
    "metabolic_completeness": 0.0到1.0之间的代谢完整性,
    "unusual_features": ["异常特征列表"],
    "phylogenetic_consistency": "与系统发育的一致性评估"
  }},
  "curation_recommendations": [
    {{
      "priority": "low/medium/high/critical",
      "action": "建议操作",
      "target": "目标基因或区域",
      "method": "推荐方法",
      "expected_outcome": "预期结果"
    }}
  ],
  "validation_strategy": {{
    "experimental_validation_needed": true/false,
    "recommended_experiments": ["推荐实验"],
    "confidence_level": 0.0到1.0之间的置信度,
    "reliability_factors": ["可靠性因素"]
  }},
  "publication_readiness": {{
    "ready": true/false,
    "confidence": 0.0到1.0之间的置信度,
    "required_improvements": ["需要改进的方面"],
    "quality_metrics": {{"指标名": 数值}}
  }},
  "next_steps": ["下一步建议"],
  "reasoning": "分析推理过程"
}}"""


class AnnotationAgent(BaseAgent):
    """基于 AI 的基因注释智能体"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("annotation", config)
        
        # Annotation 特有配置
        self.genetic_code = self.config.get("genetic_code", 2)  # 线粒体遗传密码
        self.expected_genes = {
            "protein": 13,
            "trna": 22,
            "rrna": 2,
            "total": 37
        }
        self.supported_annotators = ["mitos", "geseq", "cpgavas", "prokka"]
    
    def get_capability(self) -> AgentCapability:
        """返回 Annotation Agent 的能力描述"""
        return AgentCapability(
            name="annotation",
            description="AI-powered gene annotation analysis and quality assessment",
            supported_inputs=["assembly", "kingdom", "genetic_code"],
            supported_outputs=["annotations", "annotation_stats", "quality_report"],
            resource_requirements={
                "cpu_cores": 4,
                "memory_gb": 16,
                "disk_gb": 10,
                "estimated_time_sec": 900
            },
            dependencies=["mitos", "blast", "hmmer"]
        )
    
    def prepare(self, workdir: Path, **kwargs) -> None:
        """准备阶段 - 设置工作目录和检查工具"""
        self.workdir = workdir
        self.workdir.mkdir(parents=True, exist_ok=True)
        
        # 创建注释分析目录
        (self.workdir / "annotation").mkdir(exist_ok=True)
        
        logger.info(f"Annotation Agent prepared in {workdir}")
    
    def run(self, inputs: Dict[str, Any], **config) -> StageResult:
        """运行注释分析"""
        return self.execute_stage(inputs)
    
    def finalize(self) -> None:
        """清理和后处理"""
        logger.info("Annotation Agent finalized")
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """验证输入数据"""
        required_fields = ["assembly"]
        for field in required_fields:
            if field not in inputs:
                logger.error(f"Missing required input field: {field}")
                return False
        
        # 检查组装文件是否存在
        assembly_file = inputs.get("assembly")
        if assembly_file and not Path(assembly_file).exists():
            logger.error(f"Assembly file not found: {assembly_file}")
            return False
        
        return True
    
    def _diagnose_annotation_error(self, error_msg: str, stderr_content: str,
                                   stdout_content: str, tool_name: str) -> Dict[str, Any]:
        """
        诊断注释错误
        
        Args:
            error_msg: 异常消息
            stderr_content: 标准错误输出
            stdout_content: 标准输出
            tool_name: 工具名称
        
        Returns:
            诊断结果，包含错误类型、能否修复、修复建议
        """
        diagnosis_prompt = f"""分析以下基因注释错误：

工具: {tool_name}
异常: {error_msg}

标准错误输出（最后1000字符）:
```
{stderr_content[-1000:] if stderr_content else "无"}
```

标准输出（最后1000字符）:
```
{stdout_content[-1000:] if stdout_content else "无"}
```

请诊断：
1. 错误类型：tool_not_found/out_of_memory/timeout/parameter_error/sequence_format/tool_bug/unknown
2. 根本原因：简洁说明
3. 能否自动修复：true/false
4. 修复建议：
   - 如果是工具不可用：推荐备选工具
   - 如果是超时：增加超时时间
   - 如果是参数错误：调整genetic_code等参数
   - 如果是序列格式：无法修复

输出 JSON 格式：
{{
  "error_type": "类型",
  "root_cause": "原因",
  "can_fix": true/false,
  "fix_strategy": "retry/adjust_params/switch_tool/abort",
  "suggestions": {{
    "alternative_tool": "工具名或null",
    "parameter_adjustments": {{"参数": "值"}},
    "explanation": "为什么这样能解决"
  }}
}}"""
        
        try:
            diagnosis = self.generate_llm_json(
                prompt=diagnosis_prompt,
                schema={
                    "type": "object",
                    "properties": {
                        "error_type": {"type": "string"},
                        "root_cause": {"type": "string"},
                        "can_fix": {"type": "boolean"},
                        "fix_strategy": {"type": "string"},
                        "suggestions": {"type": "object"}
                    }
                },
                temperature=0.3
            )
            logger.info(f"🔍 Annotation Error diagnosis: {diagnosis['error_type']} - {diagnosis['root_cause']}")
            return diagnosis
        except Exception as e:
            logger.warning(f"AI diagnosis failed: {e}, using rule-based diagnosis")
            return self._rule_based_diagnosis(error_msg, stderr_content)
    
    def _rule_based_diagnosis(self, error_msg: str, stderr: str) -> Dict[str, Any]:
        """基于规则的简单错误诊断（AI 不可用时的备选）"""
        error_lower = (error_msg + " " + stderr).lower()
        
        if "not found" in error_lower or "command not found" in error_lower:
            return {
                "error_type": "tool_not_found",
                "root_cause": "Annotation tool not installed",
                "can_fix": True,
                "fix_strategy": "switch_tool",
                "suggestions": {
                    "alternative_tool": "geseq",
                    "explanation": "Try alternative annotation tool"
                }
            }
        elif "timeout" in error_lower or "timed out" in error_lower:
            return {
                "error_type": "timeout",
                "root_cause": "Annotation timeout",
                "can_fix": True,
                "fix_strategy": "adjust_params",
                "suggestions": {
                    "parameter_adjustments": {"timeout": "increase"},
                    "explanation": "Increase timeout"
                }
            }
        elif "sequence" in error_lower or "fasta" in error_lower or "format" in error_lower:
            return {
                "error_type": "sequence_format",
                "root_cause": "Input sequence format error",
                "can_fix": False,
                "fix_strategy": "abort",
                "suggestions": {
                    "explanation": "Sequence format is invalid"
                }
            }
        else:
            return {
                "error_type": "unknown",
                "root_cause": "Unknown annotation error",
                "can_fix": False,
                "fix_strategy": "abort",
                "suggestions": {}
            }
    
    def _execute_annotation_with_retry(self, inputs: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        """
        智能执行注释，包含完整的错误处理和自动修复
        
        这是 Agent 的核心能力：自己处理错误，自己尝试修复
        
        Args:
            inputs: 输入数据
            max_retries: 最大重试次数
        
        Returns:
            注释结果
        
        Raises:
            RuntimeError: 确实无法修复时抛出
        """
        retry_count = 0
        current_params = {
            "timeout": self.config.get("timeout", 3600)
        }
        current_tool = inputs.get("annotator", "mitos")
        
        while retry_count <= max_retries:
            try:
                inputs_copy = inputs.copy()
                inputs_copy["annotator"] = current_tool
                inputs_copy.update(current_params)
                
                logger.info(
                    f"🔧 Annotation attempt {retry_count + 1}/{max_retries + 1} "
                    f"with {current_tool}"
                )
                
                # 执行注释
                result = self.run_annotation(inputs_copy)
                
                logger.info(f"✅ Annotation succeeded on attempt {retry_count + 1}")
                return result
                
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                
                logger.warning(f"❌ Annotation attempt {retry_count} failed: {error_msg}")
                
                # 如果达到最大重试次数，放弃
                if retry_count > max_retries:
                    logger.error(
                        f"💔 Annotation failed after {max_retries} retries. "
                        f"Cannot auto-fix. Last error: {error_msg}"
                    )
                    raise RuntimeError(
                        f"Annotation failed after {max_retries} attempts.\n"
                        f"Tool: {current_tool}\n"
                        f"Last error: {error_msg}\n"
                        f"Please check:\n"
                        f"1. Tool installation (mitos, geseq)\n"
                        f"2. Input assembly quality\n"
                        f"3. System resources\n"
                        f"4. Logs in {self.workdir}/annotation/"
                    )
                
                # 读取错误日志
                stderr_content = ""
                stdout_content = ""
                try:
                    stderr_path = self.workdir / "annotation" / "stderr.log"
                    stdout_path = self.workdir / "annotation" / "stdout.log"
                    if stderr_path.exists():
                        stderr_content = stderr_path.read_text(encoding='utf-8', errors='ignore')
                    if stdout_path.exists():
                        stdout_content = stdout_path.read_text(encoding='utf-8', errors='ignore')
                except Exception:
                    pass
                
                # AI 诊断错误
                diagnosis = self._diagnose_annotation_error(
                    error_msg, stderr_content, stdout_content, current_tool
                )
                
                # 判断能否修复
                if not diagnosis["can_fix"]:
                    logger.error(f"💔 Error cannot be auto-fixed: {diagnosis['root_cause']}")
                    raise RuntimeError(
                        f"Annotation error cannot be automatically fixed.\n"
                        f"Error type: {diagnosis['error_type']}\n"
                        f"Root cause: {diagnosis['root_cause']}\n"
                        f"Please fix manually and retry."
                    )
                
                # 根据诊断结果修复
                fix_strategy = diagnosis["fix_strategy"]
                suggestions = diagnosis.get("suggestions", {})
                
                if fix_strategy == "switch_tool":
                    alt_tool = suggestions.get("alternative_tool")
                    if alt_tool:
                        logger.info(f"🔄 Switching from {current_tool} to {alt_tool}")
                        logger.info(f"   Reason: {suggestions.get('explanation', 'N/A')}")
                        current_tool = alt_tool
                    else:
                        logger.error("No alternative tool available")
                        continue
                
                elif fix_strategy == "adjust_params":
                    param_adjustments = suggestions.get("parameter_adjustments", {})
                    if param_adjustments:
                        adjusted = self.auto_adjust_parameters(error_msg, current_params)
                        current_params.update(adjusted)
                        logger.info(f"🔧 Adjusted parameters: {param_adjustments}")
                        logger.info(f"   Reason: {suggestions.get('explanation', 'N/A')}")
                    else:
                        logger.warning("No parameter adjustments suggested, simple retry")
                
                elif fix_strategy == "retry":
                    logger.info("🔄 Simple retry without changes")
                
                else:
                    logger.warning(f"Unknown fix strategy: {fix_strategy}, aborting")
                    raise RuntimeError(f"Unknown fix strategy: {fix_strategy}")
        
        raise RuntimeError("Unexpected error in retry loop")
    
    def execute_stage(self, inputs: Dict[str, Any]) -> StageResult:
        """执行基因注释阶段"""
        self.status = AgentStatus.RUNNING
        self.emit_event("stage_start", stage="annotation")
        
        try:
            # 验证输入
            if not self.validate_inputs(inputs):
                raise ValueError("Input validation failed")
            
            # 执行注释（带智能错误处理和重试）
            annotation_results = self._execute_annotation_with_retry(inputs, max_retries=3)
            
            # AI 分析注释结果
            ai_analysis = self.analyze_annotation_results(annotation_results)
            
            # 构建结果
            result = StageResult(
                status=AgentStatus.FINISHED,
                outputs={
                    "annotation_results": annotation_results,
                    "ai_analysis": ai_analysis,
                    "annotation_file": annotation_results.get("annotation_file"),
                    "quality_score": ai_analysis.get("annotation_quality", {}).get("overall_score", 0.7)
                },
                metrics={
                    "total_genes": annotation_results.get("total_genes", 0),
                    "protein_genes": annotation_results.get("protein_genes", 0),
                    "completeness": ai_analysis.get("completeness_analysis", {}).get("completeness_percentage", 0),
                    "quality_score": ai_analysis.get("annotation_quality", {}).get("overall_score", 0.7)
                },
                logs={"annotation_stats": self.workdir / "annotation_stats.json" if self.workdir else Path("annotation_stats.json")}
            )
            
            self.status = AgentStatus.FINISHED
            self.emit_event("stage_complete", stage="annotation", success=True)
            
            return result
            
        except Exception as e:
            logger.error(f"Annotation failed: {e}")
            self.status = AgentStatus.FAILED
            self.emit_event("stage_complete", stage="annotation", success=False, error=str(e))
            
            return StageResult(
                status=AgentStatus.FAILED,
                outputs={},
                metrics={},
                logs={},
                errors=[str(e)]
            )
    
    def run_annotation(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """运行基因注释"""
        assembly_file = inputs["assembly"]
        kingdom = inputs.get("kingdom", "animal")
        annotator = inputs.get("annotator", "mitos")
        interactive = inputs.get("interactive", False)
        
        # Plant + GeSeq路径
        if kingdom == "plant" and annotator == "geseq":
            if not interactive:
                raise AnnotationFailedError(
                    "Plant annotation with GeSeq requires interactive mode.\n"
                    "GeSeq is a web-based service that needs manual operation.\n\n"
                    "Run with: mito-forge pipeline --kingdom plant --interactive\n\n"
                    "Alternative: Install CPGAVAS2 for local annotation."
                )
            
            # 触发GeSeq向导
            from ...utils.geseq_guide import GeSeqGuide
            from .exceptions import PipelinePausedException
            
            guide = GeSeqGuide(
                assembly_path=Path(assembly_file),
                kingdom=kingdom,
                workdir=self.workdir or Path(".")
            )
            guide.display_instructions()
            guide.open_browser()
            
            # 抛出暂停异常
            raise PipelinePausedException(
                task_id=guide.task_id,
                message=f"Pipeline paused for GeSeq annotation.\n"
                        f"Resume with: mito-forge resume {guide.task_id} --annotation <result.gbk>"
            )
        
        logger.info(f"Running annotation with {annotator} on {assembly_file}")
        
        # 尝试运行真实注释工具
        try:
            import shutil
            from pathlib import Path
            
            ann_dir = (self.workdir or Path(".")) / "annotation"
            ann_dir.mkdir(parents=True, exist_ok=True)
            
            # 检查工具是否存在
            def find_tool(tool_name: str) -> str:
                if shutil.which(tool_name):
                    return tool_name
                try:
                    from ...utils.tools_manager import ToolsManager
                    tm = ToolsManager(project_root=Path.cwd())
                    p = tm.where(tool_name)
                    if p:
                        return str(p)
                except Exception:
                    pass
                return None
            
            if annotator.lower() == "mitos":
                # MITOS只支持动物(Metazoan)线粒体,不支持植物
                if kingdom != "animal":
                    raise ToolNotFoundError(
                        f"MITOS only supports animal mitochondrial genomes.\n"
                        f"For plant annotation, use GeSeq (web-based) in interactive mode:\n"
                        f"  mito-forge pipeline --kingdom plant --interactive\n"
                        f"Or install CPGAVAS2 for local annotation."
                    )
                
                exe = find_tool("runmitos.py") or find_tool("mitos")
                if exe:
                    # MITOS 参数: --input assembly.fasta --code 2 --outdir output
                    genetic_code = 2  # 动物线粒体遗传密码
                    args = [
                        "--input", str(assembly_file),
                        "--code", str(genetic_code),
                        "--outdir", str(ann_dir)
                    ]
                    rc = self.run_tool(exe, args, cwd=ann_dir)
                    if rc.get("exit_code") == 0:
                        # 解析 MITOS 输出
                        try:
                            from ...utils.parsers import parse_mitos_output
                            parsed = parse_mitos_output(ann_dir)
                            
                            if parsed['success']:
                                return {
                                    "annotator": "mitos",
                                    "genome_length": 0,  # 需要从 assembly_file 获取
                                    "kingdom": kingdom,
                                    "genetic_code": genetic_code,
                                    "annotation_file": parsed['files'].get('gff', ''),
                                    "total_genes": parsed['metrics'].get('total_genes', 0),
                                    "protein_genes": parsed['metrics'].get('cds_count', 0),
                                    "trna_genes": parsed['metrics'].get('trna_count', 0),
                                    "rrna_genes": parsed['metrics'].get('rrna_count', 0),
                                    "other_genes": 0,
                                    "coding_coverage": 0,  # 需要计算
                                    "genome_utilization": 0,
                                    "avg_gene_length": 0,
                                    "detected_issues": [],
                                    "gene_details": parsed['metrics'].get('genes', [])
                                }
                            else:
                                logger.warning(f"MITOS parsing failed: {parsed.get('errors')}")
                        except Exception as e:
                            logger.warning(f"Failed to parse MITOS output: {e}")
        except Exception as _e:
            logger.error(f"Annotation tool execution failed: {_e}")
            raise RuntimeError(
                f"Annotation failed with {annotator}. "
                f"Please ensure the tool is installed and accessible. "
                f"Error: {_e}"
            )
        
        # 如果没有返回（工具不支持或解析失败），抛出异常
        raise AnnotationFailedError(
            f"Annotation with {annotator} failed - no results returned.\n"
            f"Possible causes:\n"
            f"1. Annotator tool ({annotator}) not properly installed\n"
            f"2. Input assembly file is invalid or empty\n"
            f"3. Tool execution error\n"
            f"Install MITOS: conda install -c bioconda mitos\n"
            f"Check logs: {self.workdir}/annotation/{annotator}.stdout.log"
        )
    
    def analyze_annotation_results(self, annotation_results: Dict[str, Any]) -> Dict[str, Any]:
        """使用 AI 分析注释结果"""
        logger.info("Analyzing annotation results with AI...")
        
        # 检查 annotation_results 是否为 None
        if not annotation_results:
            logger.warning("Annotation results is None, using default values")
            annotation_results = {}
        
        # 准备分析输入
        analysis_input = {
            "annotator": annotation_results.get("annotator", "unknown"),
            "genome_length": annotation_results.get("genome_length", 0),
            "kingdom": annotation_results.get("kingdom", "animal"),
            "genetic_code": annotation_results.get("genetic_code", 2),
            "total_genes": annotation_results.get("total_genes", 0),
            "protein_genes": annotation_results.get("protein_genes", 0),
            "trna_genes": annotation_results.get("trna_genes", 0),
            "rrna_genes": annotation_results.get("rrna_genes", 0),
            "other_genes": annotation_results.get("other_genes", 0),
            "coding_coverage": annotation_results.get("coding_coverage", 0),
            "genome_utilization": annotation_results.get("genome_utilization", 0),
            "avg_gene_length": annotation_results.get("avg_gene_length", 0),
            "detected_issues": "\n".join(annotation_results.get("detected_issues", []))
        }
        
        # 构建提示词
        prompt = ANNOTATION_ANALYSIS_PROMPT.format(**analysis_input)
        detail_level = str((self.config or {}).get("detail_level") or os.getenv("MITO_DETAIL_LEVEL", "quick")).lower()
        if detail_level == "detailed":
            extra_guidance = "请输出完整且结构化的结果：每类要点尽量给出3-5条，包含关键阈值与推荐参数，推理要简洁但覆盖依据。"
        else:
            extra_guidance = "请保持精简：每类要点不超过2条，一句话总结，推理尽量短。"
        prompt = f"{prompt}\n\n### 输出风格要求\n{extra_guidance}"
        
        # 注入记忆与 RAG（自动探测，可用即启用；不可用时静默跳过）
        try:
            tags = ["annotation", analysis_input.get("annotator", "unknown")]
            mem_items = self.memory_query(tags=tags, top_k=3)
            if mem_items:
                mem_lines = ["历史摘要:"]
                for it in mem_items[:3]:
                    summ = str(it.get("summary") or it.get("value") or "")
                    if len(summ) > 200:
                        summ = summ[:200] + "..."
                    mem_lines.append(f"- {summ}")
                prompt = prompt + "\n\n" + "\n".join(mem_lines)
        except Exception:
            pass
        try:
            prompt, citations = self.rag_augment(prompt, task=self.current_task, top_k=4)
        except Exception:
            citations = []
        
        # 定义 JSON Schema
        schema = {
            "type": "object",
            "required": ["annotation_quality", "completeness_analysis", "quality_issues", "publication_readiness", "reasoning"],
            "properties": {
                "annotation_quality": {"type": "object"},
                "completeness_analysis": {"type": "object"},
                "quality_issues": {"type": "array"},
                "functional_analysis": {"type": "object"},
                "curation_recommendations": {"type": "array"},
                "validation_strategy": {"type": "object"},
                "publication_readiness": {"type": "object"},
                "next_steps": {"type": "array"},
                "reasoning": {"type": "string"}
            }
        }
        
        try:
            # 调用 AI 模型
            # 根据分级调整生成参数
            temp = 0.1 if detail_level == "quick" else 0.2
            max_tok = 1800 if detail_level == "quick" else 3500
            ai_analysis = self.generate_llm_json(
                prompt=prompt,
                system=ANNOTATION_SYSTEM_PROMPT,
                schema=schema,
                temperature=temp,
                max_tokens=max_tok
            )
            
            # 保存 AI 分析结果
            if self.workdir:
                analysis_file = self.workdir / "annotation_ai_analysis.json"
                with open(analysis_file, 'w', encoding='utf-8') as f:
                    json.dump(ai_analysis, f, indent=2, ensure_ascii=False)
            
            # 写长期记忆（Mem0），包含注释质量评估摘要与引用（若有）
            try:
                aq = ai_analysis.get("annotation_quality", {}) if isinstance(ai_analysis, dict) else {}
                summary = aq.get("summary")
                score = aq.get("overall_score")
                grade = aq.get("grade")
                self.memory_write({
                    "agent": "annotation",
                    "task_id": (self.current_task.task_id if self.current_task else "annotation"),
                    "tags": ["annotation", analysis_input.get("annotator","unknown")],
                    "summary": summary or "",
                    "metrics": {"score": score, "grade": grade},
                    "citations": citations if isinstance(citations, list) else [],
                })
            except Exception:
                pass
            
            # 注入 RAG 引用到分析结果
            try:
                if isinstance(ai_analysis, dict) and isinstance(citations, list) and citations:
                    ai_analysis["references"] = citations
            except Exception:
                pass
            return ai_analysis
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            # 返回基础分析结果并注入引用
            citations = citations if isinstance(citations, list) else []
            basic = self._get_basic_analysis(annotation_results)
            try:
                if citations:
                    basic["references"] = citations
                aq = basic.get("annotation_quality", {}) if isinstance(basic, dict) else {}
                summary = aq.get("summary")
                score = aq.get("overall_score")
                grade = aq.get("grade")
                self.memory_write({
                    "agent": "annotation",
                    "task_id": (self.current_task.task_id if self.current_task else "annotation"),
                    "tags": ["annotation", annotation_results.get("annotator","unknown")],
                    "summary": summary or "",
                    "metrics": {"score": score, "grade": grade},
                    "citations": citations,
                })
            except Exception:
                pass
            return basic
    
    def _get_basic_analysis(self, annotation_results: Dict[str, Any]) -> Dict[str, Any]:
        """当 AI 分析失败时的基础分析"""
        total_genes = annotation_results.get("total_genes", 0)
        protein_genes = annotation_results.get("protein_genes", 0)
        trna_genes = annotation_results.get("trna_genes", 0)
        rrna_genes = annotation_results.get("rrna_genes", 0)
        
        # 计算完整性
        protein_complete = protein_genes >= self.expected_genes["protein"] * 0.9
        trna_complete = trna_genes >= self.expected_genes["trna"] * 0.9
        rrna_complete = rrna_genes >= self.expected_genes["rrna"]
        
        completeness = (
            (protein_genes / self.expected_genes["protein"]) * 0.5 +
            (trna_genes / self.expected_genes["trna"]) * 0.3 +
            (rrna_genes / self.expected_genes["rrna"]) * 0.2
        )
        completeness = min(1.0, completeness) * 100
        
        # 基于规则的质量评估
        if completeness >= 95 and protein_complete and trna_complete and rrna_complete:
            grade = "A"
            score = 0.9
        elif completeness >= 85 and protein_complete and (trna_complete or rrna_complete):
            grade = "B"
            score = 0.8
        elif completeness >= 70:
            grade = "C"
            score = 0.6
        else:
            grade = "D"
            score = 0.4
        
        return {
            "annotation_quality": {
                "overall_score": score,
                "grade": grade,
                "summary": f"基于规则的注释评估：完整性 {completeness:.1f}%, 总基因数 {total_genes}"
            },
            "completeness_analysis": {
                "protein_genes_complete": protein_complete,
                "trna_genes_complete": trna_complete,
                "rrna_genes_complete": rrna_complete,
                "missing_genes": [],
                "extra_genes": [],
                "completeness_percentage": completeness
            },
            "quality_issues": [],
            "functional_analysis": {
                "essential_pathways_covered": protein_complete,
                "metabolic_completeness": min(1.0, protein_genes / self.expected_genes["protein"]),
                "unusual_features": [],
                "phylogenetic_consistency": "需要进一步验证"
            },
            "curation_recommendations": [
                {
                    "priority": "medium",
                    "action": "手动检查基因边界",
                    "target": "所有基因",
                    "method": "序列比对验证",
                    "expected_outcome": "提高注释准确性"
                }
            ],
            "validation_strategy": {
                "experimental_validation_needed": score < 0.8,
                "recommended_experiments": ["RT-PCR验证", "蛋白质组学"],
                "confidence_level": 0.7,
                "reliability_factors": ["基于规则的简单评估"]
            },
            "publication_readiness": {
                "ready": score >= 0.7,
                "confidence": 0.7,
                "required_improvements": ["手动校正", "实验验证"] if score < 0.8 else [],
                "quality_metrics": {
                    "completeness": completeness,
                    "gene_count": total_genes
                }
            },
            "next_steps": ["手动校正注释", "生成最终报告"],
            "reasoning": "使用基于规则的备用分析方法"
        }