"""
质量控制智能体 - 基于 AI 的数据质量分析
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from .base_agent import BaseAgent
from .types import AgentStatus, StageResult, AgentCapability
from .exceptions import QCFailedError, ToolNotFoundError
from ...utils.logging import get_logger

logger = get_logger(__name__)

# QC 分析系统提示词
QC_SYSTEM_PROMPT = """你是一个专业的生物信息学质量控制专家，负责分析测序数据的质量并提供改进建议。

你的职责：
1. 分析测序数据的质量指标（质量分数、GC含量、长度分布等）
2. 识别潜在的问题（接头污染、质量下降、偏差等）
3. 推荐合适的质量控制和数据预处理策略
4. 评估数据是否适合后续分析

请严格按照 JSON 格式输出，不要包含任何其他文本。"""

# QC 分析提示词模板
QC_ANALYSIS_PROMPT = """请分析以下测序数据的质量控制结果：

## 数据基本信息
- 文件名: {filename}
- 读长类型: {read_type}
- 总读数: {total_reads}
- 总碱基数: {total_bases}
- 平均读长: {avg_length}

## 质量指标
- 平均质量分数: {avg_quality}
- Q20 百分比: {q20_percent}%
- Q30 百分比: {q30_percent}%
- GC 含量: {gc_content}%

## 长度分布
- 最短读长: {min_length}
- 最长读长: {max_length}
- N50: {n50}

## 检测到的问题
{detected_issues}

请输出包含以下字段的 JSON：
{{
  "quality_assessment": {{
    "overall_score": 0.0到1.0之间的总体质量评分,
    "grade": "A/B/C/D/F等级评定",
    "summary": "质量评估总结"
  }},
  "issues_found": [
    {{
      "type": "问题类型",
      "severity": "low/medium/high/critical",
      "description": "问题描述",
      "affected_percentage": 百分比数值
    }}
  ],
  "recommendations": [
    {{
      "action": "建议操作",
      "tool": "推荐工具",
      "parameters": {{"参数名": "参数值"}},
      "priority": "low/medium/high",
      "expected_improvement": "预期改善效果"
    }}
  ],
  "preprocessing_strategy": {{
    "trimming_needed": true/false,
    "filtering_needed": true/false,
    "adapter_removal": true/false,
    "quality_threshold": 数值,
    "length_threshold": 数值
  }},
  "suitability": {{
    "for_assembly": true/false,
    "for_annotation": true/false,
    "confidence": 0.0到1.0之间的置信度,
    "limiting_factors": ["限制因素列表"]
  }},
  "next_steps": ["下一步建议"],
  "reasoning": "分析推理过程"
}}"""


class QCAgent(BaseAgent):
    """基于 AI 的质量控制智能体"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("qc", config)
        
        # QC 特有配置
        self.quality_threshold = self.config.get("quality_threshold", 20)
        self.length_threshold = self.config.get("length_threshold", 100)
        self.supported_tools = ["fastqc", "nanoplot", "trimmomatic", "cutadapt"]
    
    def get_capability(self) -> AgentCapability:
        """返回 QC Agent 的能力描述"""
        return AgentCapability(
            name="qc",
            description="AI-powered quality control analysis for sequencing data",
            supported_inputs=["reads", "read_type"],
            supported_outputs=["qc_report", "quality_metrics", "recommendations"],
            resource_requirements={
                "cpu_cores": 4,
                "memory_gb": 8,
                "disk_gb": 5,
                "estimated_time_sec": 300
            },
            dependencies=["fastqc", "nanoplot"]
        )
    
    def prepare(self, workdir: Path, **kwargs) -> None:
        """准备阶段 - 设置工作目录和检查工具"""
        self.workdir = workdir
        self.workdir.mkdir(parents=True, exist_ok=True)
        
        # 创建 QC 分析目录
        (self.workdir / "qc").mkdir(exist_ok=True)
        
        logger.info(f"QC Agent prepared in {workdir}")
    
    def run(self, inputs: Dict[str, Any], **config) -> StageResult:
        """运行 QC 分析"""
        return self.execute_stage(inputs)
    
    def finalize(self) -> None:
        """清理和后处理"""
        logger.info("QC Agent finalized")
    
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
    
    def _diagnose_qc_error(self, error_msg: str, stderr_content: str,
                          stdout_content: str, tool_name: str) -> Dict[str, Any]:
        """
        诊断 QC 错误
        
        Args:
            error_msg: 异常消息
            stderr_content: 标准错误输出
            stdout_content: 标准输出
            tool_name: 工具名称
        
        Returns:
            诊断结果，包含错误类型、能否修复、修复建议
        """
        diagnosis_prompt = f"""分析以下质量控制错误：

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
1. 错误类型：tool_not_found/out_of_memory/timeout/parameter_error/data_format/tool_bug/unknown
2. 根本原因：简洁说明
3. 能否自动修复：true/false
4. 修复建议：
   - 如果是工具不可用：推荐备选工具
   - 如果是内存不足：减少线程
   - 如果是格式错误：尝试其他工具
   - 如果是数据问题：无法修复

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
            logger.info(f"🔍 QC Error diagnosis: {diagnosis['error_type']} - {diagnosis['root_cause']}")
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
                "root_cause": "QC tool not installed",
                "can_fix": True,
                "fix_strategy": "switch_tool",
                "suggestions": {
                    "alternative_tool": "nanoplot",
                    "explanation": "Try alternative QC tool"
                }
            }
        elif "out of memory" in error_lower or "oom" in error_lower:
            return {
                "error_type": "out_of_memory",
                "root_cause": "Memory exhausted",
                "can_fix": True,
                "fix_strategy": "adjust_params",
                "suggestions": {
                    "parameter_adjustments": {"threads": "reduce_half"},
                    "explanation": "Reduce threads to save memory"
                }
            }
        elif "format" in error_lower or "invalid" in error_lower:
            return {
                "error_type": "data_format",
                "root_cause": "Input format error",
                "can_fix": False,
                "fix_strategy": "abort",
                "suggestions": {
                    "explanation": "Input data format is invalid"
                }
            }
        else:
            return {
                "error_type": "unknown",
                "root_cause": "Unknown QC error",
                "can_fix": False,
                "fix_strategy": "abort",
                "suggestions": {}
            }
    
    def _execute_qc_with_retry(self, inputs: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        """
        智能执行 QC，包含完整的错误处理和自动修复
        
        这是 Agent 的核心能力：自己处理错误，自己尝试修复
        
        Args:
            inputs: 输入数据
            max_retries: 最大重试次数
        
        Returns:
            QC 结果
        
        Raises:
            RuntimeError: 确实无法修复时抛出
        """
        retry_count = 0
        current_params = {
            "threads": int(self.config.get("threads", 4))
        }
        current_tool = inputs.get("qc_tool", "fastqc")
        
        while retry_count <= max_retries:
            try:
                inputs_copy = inputs.copy()
                inputs_copy["qc_tool"] = current_tool
                inputs_copy.update(current_params)
                
                logger.info(
                    f"🔧 QC attempt {retry_count + 1}/{max_retries + 1} "
                    f"with {current_tool}"
                )
                
                # 执行 QC
                result = self.run_qc_analysis(inputs_copy)
                
                logger.info(f"✅ QC succeeded on attempt {retry_count + 1}")
                return result
                
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                
                logger.warning(f"❌ QC attempt {retry_count} failed: {error_msg}")
                
                # 如果达到最大重试次数，放弃
                if retry_count > max_retries:
                    logger.error(
                        f"💔 QC failed after {max_retries} retries. "
                        f"Cannot auto-fix. Last error: {error_msg}"
                    )
                    raise RuntimeError(
                        f"QC analysis failed after {max_retries} attempts.\n"
                        f"Tool: {current_tool}\n"
                        f"Last error: {error_msg}\n"
                        f"Please check:\n"
                        f"1. Tool installation (fastqc, nanoplot)\n"
                        f"2. Input data format and integrity\n"
                        f"3. System resources\n"
                        f"4. Logs in {self.workdir}/qc/"
                    )
                
                # 读取错误日志
                stderr_content = ""
                stdout_content = ""
                try:
                    stderr_path = self.workdir / "qc" / "stderr.log"
                    stdout_path = self.workdir / "qc" / "stdout.log"
                    if stderr_path.exists():
                        stderr_content = stderr_path.read_text(encoding='utf-8', errors='ignore')
                    if stdout_path.exists():
                        stdout_content = stdout_path.read_text(encoding='utf-8', errors='ignore')
                except Exception:
                    pass
                
                # AI 诊断错误
                diagnosis = self._diagnose_qc_error(
                    error_msg, stderr_content, stdout_content, current_tool
                )
                
                # 判断能否修复
                if not diagnosis["can_fix"]:
                    logger.error(f"💔 Error cannot be auto-fixed: {diagnosis['root_cause']}")
                    raise RuntimeError(
                        f"QC error cannot be automatically fixed.\n"
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
        """执行质量控制分析阶段"""
        self.status = AgentStatus.RUNNING
        self.emit_event("stage_start", stage="qc_analysis")
        
        try:
            # 验证输入
            if not self.validate_inputs(inputs):
                raise ValueError("Input validation failed")
            
            # 执行 QC 分析（带智能错误处理和重试）
            qc_results = self._execute_qc_with_retry(inputs, max_retries=3)
            
            # AI 分析结果
            ai_analysis = self.analyze_qc_results(qc_results)
            
            # 构建结果
            result = StageResult(
                status=AgentStatus.FINISHED,
                outputs={
                    "qc_results": qc_results,
                    "ai_analysis": ai_analysis,
                    "quality_score": ai_analysis.get("quality_assessment", {}).get("overall_score", 0.7),
                    "reads": inputs["reads"],
                    "reads2": inputs.get("reads2")
                },
                metrics={
                    "quality_score": ai_analysis.get("quality_assessment", {}).get("overall_score", 0.7),
                    "issues_count": len(ai_analysis.get("issues_found", [])),
                    "recommendations_count": len(ai_analysis.get("recommendations", []))
                },
                logs={"qc_report": self.workdir / "qc_results.json" if self.workdir else Path("qc_results.json")}
            )
            
            self.status = AgentStatus.FINISHED
            self.emit_event("stage_complete", stage="qc_analysis", success=True)
            
            return result
            
        except Exception as e:
            logger.error(f"QC analysis failed: {e}")
            self.status = AgentStatus.FAILED
            self.emit_event("stage_complete", stage="qc_analysis", success=False, error=str(e))
            
            return StageResult(
                status=AgentStatus.FAILED,
                outputs={},
                metrics={},
                logs={},
                errors=[str(e)]
            )
    
    def run_qc_analysis(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """运行基础 QC 分析工具"""
        reads_file = inputs["reads"]
        reads2_file = inputs.get("reads2")  # 双端测序 R2
        read_type = inputs.get("read_type", "illumina")
        
        if reads2_file:
            logger.info(f"Running QC analysis on paired-end data: {reads_file} + {reads2_file}")
        else:
            logger.info(f"Running QC analysis on {reads_file}")
        # 优先尝试真实工具：fastqc 或 NanoPlot
        try:
            import shutil
            qc_dir = (self.workdir or Path(".")) / "qc"
            qc_dir.mkdir(parents=True, exist_ok=True)
            # 简单策略：Illumina 优先 fastqc，其他优先 NanoPlot
            prefer_fastqc = (str(read_type).lower() == "illumina")
            
            # 检查工具是否存在（系统 PATH 或项目本地）
            def tool_exists(tool_name: str) -> bool:
                if shutil.which(tool_name):
                    return True
                try:
                    from ...utils.tools_manager import ToolsManager
                    tm = ToolsManager(project_root=Path.cwd())
                    return tm.where(tool_name) is not None
                except Exception:
                    return False
            
            fastqc_exists = tool_exists("fastqc")
            nanoplot_exists = tool_exists("NanoPlot") or tool_exists("nanoplot")
            if self.config.get("dry_run"):
                pass  # run_tool 内部会处理
            if prefer_fastqc and fastqc_exists:
                # 运行 FastQC for R1
                rc1 = self.run_tool("fastqc", ["-o", str(qc_dir.absolute()), str(Path(reads_file).absolute())], cwd=qc_dir)
                
                # 如果是双端数据，也对 R2 运行 QC
                if reads2_file and rc1.get("exit_code") == 0:
                    rc2 = self.run_tool("fastqc", ["-o", str(qc_dir.absolute()), str(Path(reads2_file).absolute())], cwd=qc_dir)
                
                if rc1.get("exit_code") == 0:
                    # 解析 FastQC 输出
                    try:
                        from ...utils.parsers import find_fastqc_output, parse_fastqc_output
                        zip_file_r1 = find_fastqc_output(qc_dir, Path(reads_file))
                        
                        if zip_file_r1 and zip_file_r1.exists():
                            result_r1 = parse_fastqc_output(zip_file_r1)
                            result_r1["read_type"] = read_type
                            
                            # 如果有 R2，解析并合并
                            if reads2_file:
                                zip_file_r2 = find_fastqc_output(qc_dir, Path(reads2_file))
                                if zip_file_r2 and zip_file_r2.exists():
                                    result_r2 = parse_fastqc_output(zip_file_r2)
                                    # 合并 R1 和 R2 的指标
                                    from ...utils.paired_end_utils import merge_paired_qc_metrics
                                    if result_r1.get('success') and result_r2.get('success'):
                                        merged = merge_paired_qc_metrics(result_r1['metrics'], result_r2['metrics'])
                                        merged["read_type"] = read_type
                                        return merged
                            
                            # 单端或 R2 解析失败时返回 R1 结果
                            result = result_r1
                            return result
                        else:
                            raise QCFailedError(
                                f"FastQC output not found: {qc_dir}\n"
                                f"FastQC may have failed to execute properly.\n"
                                f"Check logs: {qc_dir}/fastqc.stderr.log\n"
                                f"Ensure FastQC is properly installed: conda install -c bioconda fastqc"
                            )
                    except Exception as e:
                        raise QCFailedError(
                            f"Failed to parse FastQC output: {e}\n"
                            f"Output directory: {qc_dir}\n"
                            f"Check if FastQC completed successfully."
                        )
            if nanoplot_exists:
                exe = "NanoPlot" if shutil.which("NanoPlot") else "nanoplot"
                rc = self.run_tool(exe, ["--fastq", str(reads_file), "-o", str(qc_dir)], cwd=qc_dir)
                if rc.get("exit_code") == 0:
                    # 解析 NanoPlot 输出
                    try:
                        from ...utils.parsers import parse_nanoplot_output
                        parsed = parse_nanoplot_output(qc_dir)
                        
                        if parsed['success']:
                            return {
                                "filename": Path(reads_file).name,
                                "read_type": read_type,
                                "total_reads": parsed['metrics'].get('total_reads', 0),
                                "total_bases": parsed['metrics'].get('total_bases', 0),
                                "avg_length": parsed['metrics'].get('avg_length', 0),
                                "avg_quality": parsed['metrics'].get('avg_quality', 0),
                                "q20_percent": parsed['metrics'].get('q20_percent', 0),
                                "gc_content": parsed['metrics'].get('gc_content', 0),
                                "n50": parsed['metrics'].get('n50', 0),
                                "detected_issues": []
                            }
                        else:
                            logger.warning(f"NanoPlot parsing failed: {parsed.get('errors')}")
                    except Exception as e:
                        logger.warning(f"Failed to parse NanoPlot output: {e}")
        except Exception as _e:
            logger.error(f"QC tool execution failed: {_e}")
            raise RuntimeError(
                f"QC analysis failed. "
                f"Please ensure FastQC/NanoPlot is installed and accessible. "
                f"Error: {_e}"
            )
    
    def analyze_qc_results(self, qc_results: Dict[str, Any]) -> Dict[str, Any]:
        """使用 AI 分析 QC 结果"""
        logger.info("Analyzing QC results with AI...")
        
        # 准备分析输入
        # 格式化 detected_issues
        detected_issues_list = qc_results.get("detected_issues", [])
        if detected_issues_list and isinstance(detected_issues_list[0], dict):
            # 新格式：列表of dict
            detected_issues_str = "\n".join([
                f"- {issue.get('type', 'Unknown')}: {issue.get('description', '')} (severity: {issue.get('severity', 'unknown')})"
                for issue in detected_issues_list
            ])
        else:
            # 旧格式：列表 of str
            detected_issues_str = "\n".join(detected_issues_list)
        
        analysis_input = {
            "filename": qc_results.get("filename", "unknown"),
            "read_type": qc_results.get("read_type", "unknown"),
            "total_reads": qc_results.get("total_reads", 0),
            "total_bases": qc_results.get("total_bases", 0),
            "avg_length": qc_results.get("avg_length", 0),
            "avg_quality": qc_results.get("avg_quality", 0),
            "q20_percent": qc_results.get("q20_percent", 0),
            "q30_percent": qc_results.get("q30_percent", 0),
            "gc_content": qc_results.get("gc_content", 0),
            "min_length": qc_results.get("min_length", 0),
            "max_length": qc_results.get("max_length", 0),
            "n50": qc_results.get("n50", 0),
            "detected_issues": detected_issues_str
        }
        
        # 构建提示词
        prompt = QC_ANALYSIS_PROMPT.format(**analysis_input)
        detail_level = str((self.config or {}).get("detail_level") or os.getenv("MITO_DETAIL_LEVEL", "quick")).lower()
        if detail_level == "detailed":
            extra_guidance = "请输出完整且结构化的结果：每类要点尽量给出3-5条，包含关键阈值与推荐参数，推理要简洁但覆盖依据。"
        else:
            extra_guidance = "请保持精简：每类要点不超过2条，一句话总结，推理尽量短。"
        prompt = f"{prompt}\n\n### 输出风格要求\n{extra_guidance}"
        
        # 注入记忆与 RAG（自动探测，可用即启用；不可用时静默跳过）
        try:
            tags = ["qc", analysis_input.get("filename", "unknown")]
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
            "required": ["quality_assessment", "issues_found", "recommendations", "suitability", "reasoning"],
            "properties": {
                "quality_assessment": {"type": "object"},
                "issues_found": {"type": "array"},
                "recommendations": {"type": "array"},
                "preprocessing_strategy": {"type": "object"},
                "suitability": {"type": "object"},
                "next_steps": {"type": "array"},
                "reasoning": {"type": "string"}
            }
        }
        
        try:
            # 调用 AI 模型
            # 根据分级调整生成参数
            temp = 0.1 if detail_level == "quick" else 0.2
            max_tok = 1500 if detail_level == "quick" else 3200
            ai_analysis = self.generate_llm_json(
                prompt=prompt,
                system=QC_SYSTEM_PROMPT,
                schema=schema,
                temperature=temp,
                max_tokens=max_tok
            )
            
            # 保存 AI 分析结果
            if self.workdir:
                analysis_file = self.workdir / "qc_ai_analysis.json"
                with open(analysis_file, 'w', encoding='utf-8') as f:
                    json.dump(ai_analysis, f, indent=2, ensure_ascii=False)
            
            # 写长期记忆（Mem0），包含质量评估摘要与引用（若有）
            try:
                qa = ai_analysis.get("quality_assessment", {}) if isinstance(ai_analysis, dict) else {}
                summary = qa.get("summary")
                score = qa.get("overall_score")
                grade = qa.get("grade")
                self.memory_write({
                    "agent": "qc",
                    "task_id": (self.current_task.task_id if self.current_task else "qc"),
                    "tags": ["qc", analysis_input.get("filename","unknown")],
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
            basic = self._get_basic_analysis(qc_results)
            try:
                if citations:
                    basic["references"] = citations
                qa = basic.get("quality_assessment", {}) if isinstance(basic, dict) else {}
                summary = qa.get("summary")
                score = qa.get("overall_score")
                grade = qa.get("grade")
                self.memory_write({
                    "agent": "qc",
                    "task_id": (self.current_task.task_id if self.current_task else "qc"),
                    "tags": ["qc", qc_results.get("filename","unknown")],
                    "summary": summary or "",
                    "metrics": {"score": score, "grade": grade},
                    "citations": citations,
                })
            except Exception:
                pass
            return basic
    
    def _get_basic_analysis(self, qc_results: Dict[str, Any]) -> Dict[str, Any]:
        """当 AI 分析失败时的基础分析"""
        avg_quality = qc_results.get("avg_quality", 0)
        q30_percent = qc_results.get("q30_percent", 0)
        
        # 基于规则的质量评估
        if avg_quality >= 30 and q30_percent >= 85:
            grade = "A"
            score = 0.9
        elif avg_quality >= 25 and q30_percent >= 75:
            grade = "B"
            score = 0.8
        elif avg_quality >= 20 and q30_percent >= 60:
            grade = "C"
            score = 0.6
        else:
            grade = "D"
            score = 0.4
        
        return {
            "quality_assessment": {
                "overall_score": score,
                "grade": grade,
                "summary": f"基于规则的质量评估：平均质量 {avg_quality}, Q30 {q30_percent}%"
            },
            "issues_found": [],
            "recommendations": [
                {
                    "action": "质量过滤",
                    "tool": "trimmomatic",
                    "parameters": {"quality_threshold": self.quality_threshold},
                    "priority": "medium",
                    "expected_improvement": "提高数据质量"
                }
            ],
            "preprocessing_strategy": {
                "trimming_needed": avg_quality < 25,
                "filtering_needed": q30_percent < 80,
                "adapter_removal": True,
                "quality_threshold": self.quality_threshold,
                "length_threshold": self.length_threshold
            },
            "suitability": {
                "for_assembly": score >= 0.6,
                "for_annotation": score >= 0.7,
                "confidence": 0.7,
                "limiting_factors": ["基于规则的简单评估"]
            },
            "next_steps": ["进行数据预处理", "运行组装分析"],
            "reasoning": "使用基于规则的备用分析方法"
        }