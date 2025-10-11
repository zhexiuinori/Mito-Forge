"""
组装智能体 - 基于 AI 的基因组组装分析
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from .base_agent import BaseAgent
from .types import AgentStatus, StageResult, AgentCapability
from ...utils.logging import get_logger

logger = get_logger(__name__)

# 组装分析系统提示词
ASSEMBLY_SYSTEM_PROMPT = """你是一个专业的生物信息学基因组组装专家，负责分析组装结果并提供优化建议。

你的职责：
1. 评估组装质量指标（N50、连续性、完整性等）
2. 识别组装问题（碎片化、错误、缺失等）
3. 推荐组装优化策略和后续处理步骤
4. 评估组装结果是否适合注释分析

请严格按照 JSON 格式输出，不要包含任何其他文本。"""

# 组装分析提示词模板
ASSEMBLY_ANALYSIS_PROMPT = """请分析以下基因组组装结果：

## 组装基本信息
- 组装工具: {assembler}
- 输入数据类型: {read_type}
- 目标物种: {kingdom}
- 组装时间: {assembly_time}分钟

## 组装统计
- 总序列数: {num_contigs}
- 总长度: {total_length} bp
- 最长序列: {max_length} bp
- N50: {n50} bp
- N90: {n90} bp
- GC含量: {gc_content}%

## 质量指标
- 覆盖度: {coverage}x
- 完整性评估: {completeness}%
- 污染评估: {contamination}%

## 预期目标
- 线粒体基因组预期长度: 16000-17000 bp
- 预期基因数量: 37个基因
- 预期结构: 环状单分子

请输出包含以下字段的 JSON：
{{
  "assembly_quality": {{
    "overall_score": 0.0到1.0之间的总体质量评分,
    "grade": "A/B/C/D/F等级评定",
    "summary": "组装质量总结"
  }},
  "structural_analysis": {{
    "is_circular": true/false,
    "is_complete": true/false,
    "fragmentation_level": "low/medium/high",
    "main_contigs": 主要序列数量,
    "target_achieved": true/false
  }},
  "issues_found": [
    {{
      "type": "问题类型",
      "severity": "low/medium/high/critical",
      "description": "问题描述",
      "affected_regions": "影响区域"
    }}
  ],
  "optimization_recommendations": [
    {{
      "strategy": "优化策略",
      "tool": "推荐工具",
      "parameters": {{"参数名": "参数值"}},
      "priority": "low/medium/high",
      "expected_improvement": "预期改善效果"
    }}
  ],
  "polishing_strategy": {{
    "needed": true/false,
    "recommended_tools": ["工具列表"],
    "iterations": 建议迭代次数,
    "expected_improvement": "预期改善"
  }},
  "annotation_readiness": {{
    "ready": true/false,
    "confidence": 0.0到1.0之间的置信度,
    "limiting_factors": ["限制因素列表"],
    "recommended_preprocessing": ["预处理建议"]
  }},
  "next_steps": ["下一步建议"],
  "reasoning": "分析推理过程"
}}"""


class AssemblyAgent(BaseAgent):
    """基于 AI 的基因组组装智能体"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("assembly", config)
        
        # Assembly 特有配置
        self.target_length = self.config.get("target_length", 16500)  # 线粒体基因组预期长度
        self.min_contig_length = self.config.get("min_contig_length", 1000)
        self.supported_assemblers = ["spades", "flye", "unicycler", "hifiasm", "miniasm", "canu"]
    
    def get_capability(self) -> AgentCapability:
        """返回 Assembly Agent 的能力描述"""
        return AgentCapability(
            name="assembly",
            description="AI-powered genome assembly analysis and optimization",
            supported_inputs=["reads", "read_type", "kingdom"],
            supported_outputs=["assembly", "assembly_stats", "optimization_plan"],
            resource_requirements={
                "cpu_cores": 8,
                "memory_gb": 32,
                "disk_gb": 20,
                "estimated_time_sec": 1800
            },
            dependencies=["spades", "flye", "quast"]
        )
    
    def prepare(self, workdir: Path, **kwargs) -> None:
        """准备阶段 - 设置工作目录和检查工具"""
        self.workdir = workdir
        self.workdir.mkdir(parents=True, exist_ok=True)
        
        # 创建组装分析目录
        (self.workdir / "assembly").mkdir(exist_ok=True)
        
        logger.info(f"Assembly Agent prepared in {workdir}")
    
    def run(self, inputs: Dict[str, Any], **config) -> StageResult:
        """运行组装分析"""
        return self.execute_stage(inputs)
    
    def finalize(self) -> None:
        """清理和后处理"""
        logger.info("Assembly Agent finalized")
    
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
        """执行基因组组装阶段"""
        self.status = AgentStatus.RUNNING
        self.emit_event("stage_start", stage="assembly")
        
        try:
            # 验证输入
            if not self.validate_inputs(inputs):
                raise ValueError("Input validation failed")
            
            # 执行组装
            assembly_results = self.run_assembly(inputs)
            
            # AI 分析组装结果
            ai_analysis = self.analyze_assembly_results(assembly_results)
            
            # 构建结果
            result = StageResult(
                status=AgentStatus.FINISHED,
                outputs={
                    "assembly_results": assembly_results,
                    "ai_analysis": ai_analysis,
                    "assembly_file": assembly_results.get("assembly_file"),
                    "quality_score": ai_analysis.get("assembly_quality", {}).get("overall_score", 0.7)
                },
                metrics={
                    "n50": assembly_results.get("n50", 0),
                    "total_length": assembly_results.get("total_length", 0),
                    "num_contigs": assembly_results.get("num_contigs", 0),
                    "quality_score": ai_analysis.get("assembly_quality", {}).get("overall_score", 0.7)
                },
                logs={"assembly_stats": self.workdir / "assembly_stats.json" if self.workdir else Path("assembly_stats.json")}
            )
            
            self.status = AgentStatus.FINISHED
            self.emit_event("stage_complete", stage="assembly", success=True)
            
            return result
            
        except Exception as e:
            logger.error(f"Assembly failed: {e}")
            self.status = AgentStatus.FAILED
            self.emit_event("stage_complete", stage="assembly", success=False, error=str(e))
            
            return StageResult(
                status=AgentStatus.FAILED,
                outputs={},
                metrics={},
                logs={},
                errors=[str(e)]
            )
    
    def run_assembly(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """运行基因组组装"""
        reads_file = inputs["reads"]
        reads2_file = inputs.get("reads2")  # 双端测序 R2
        read_type = inputs.get("read_type", "illumina")
        assembler = inputs.get("assembler", "spades")
        
        if reads2_file:
            logger.info(f"Running assembly with {assembler} on paired-end data: {reads_file} + {reads2_file}")
        else:
            logger.info(f"Running assembly with {assembler} on {reads_file}")
        # 优先尝试真实工具，失败则回退模拟
        try:
            import shutil
            asm_dir = (self.workdir or Path(".")) / "assembly"
            asm_dir.mkdir(parents=True, exist_ok=True)
            threads = int(self.config.get("threads", 4))
            
            # 检查工具是否存在（系统 PATH 或项目本地）
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
            
            if assembler.lower() in ("spades", "spades.py"):
                exe = find_tool("spades.py") or find_tool("spades")
                if exe:
                    # 判断单端还是双端
                    if reads2_file:
                        # 双端模式: -1 R1 -2 R2
                        args = ["-1", str(reads_file), "-2", str(reads2_file), 
                                "-o", str(asm_dir), "-t", str(threads)]
                    else:
                        # 单端模式: -s reads
                        args = ["-s", str(reads_file), 
                                "-o", str(asm_dir), "-t", str(threads)]
                    rc = self.run_tool(exe, args, cwd=asm_dir)
                    if rc.get("exit_code") == 0:
                        # 解析 SPAdes 输出
                        try:
                            from ...utils.parsers import parse_spades_output
                            parsed = parse_spades_output(asm_dir)
                            
                            if parsed['success']:
                                # 转换为 Agent 期望的格式
                                return {
                                    "assembler": "spades",
                                    "read_type": read_type,
                                    "kingdom": inputs.get("kingdom", "animal"),
                                    "assembly_time": parsed['metrics'].get('assembly_time_seconds', 0),
                                    "assembly_file": str(asm_dir / "contigs.fasta"),
                                    "num_contigs": parsed['metrics'].get('num_contigs', 0),
                                    "total_length": parsed['metrics'].get('total_length', 0),
                                    "max_length": parsed['metrics'].get('max_contig_length', 0),
                                    "n50": parsed['metrics'].get('n50', 0),
                                    "n90": parsed['metrics'].get('n90', 0),
                                    "gc_content": parsed['metrics'].get('gc_content', 0),
                                    "coverage": parsed['metrics'].get('average_coverage', 0),
                                    "completeness": 0,  # 需要单独评估
                                    "contamination": 0   # 需要单独评估
                                }
                            else:
                                logger.warning(f"SPAdes parsing failed: {parsed.get('errors')}")
                        except Exception as e:
                            logger.warning(f"Failed to parse SPAdes output: {e}")
            if assembler.lower() == "flye":
                exe = find_tool("flye")
                if exe:
                    # 简化：假设 nanopore
                    args = ["--nano-raw", str(reads_file), "-o", str(asm_dir), "--threads", str(threads)]
                    rc = self.run_tool(exe, args, cwd=asm_dir)
                    if rc.get("exit_code") == 0:
                        # 解析 Flye 输出
                        try:
                            from ...utils.parsers import parse_flye_output
                            parsed = parse_flye_output(asm_dir)
                            
                            if parsed['success']:
                                return {
                                    "assembler": "flye",
                                    "read_type": read_type,
                                    "kingdom": inputs.get("kingdom", "animal"),
                                    "assembly_time": parsed['metrics'].get('assembly_time_seconds', 0),
                                    "assembly_file": str(asm_dir / "assembly.fasta"),
                                    "num_contigs": parsed['metrics'].get('num_contigs', 0),
                                    "total_length": parsed['metrics'].get('total_length', 0),
                                    "max_length": parsed['metrics'].get('max_contig_length', 0),
                                    "n50": parsed['metrics'].get('n50', 0),
                                    "n90": parsed['metrics'].get('n90', 0),
                                    "gc_content": parsed['metrics'].get('gc_content', 0),
                                    "coverage": parsed['metrics'].get('average_coverage', 0),
                                    "num_circular": parsed['metrics'].get('num_circular', 0),
                                    "completeness": 0,
                                    "contamination": 0
                                }
                            else:
                                logger.warning(f"Flye parsing failed: {parsed.get('errors')}")
                        except Exception as e:
                            logger.warning(f"Failed to parse Flye output: {e}")
            if assembler.lower() in ("getorganelle", "get_organelle_from_reads.py"):
                exe = find_tool("get_organelle_from_reads.py") or find_tool("getorganelle")
                if exe:
                    # GetOrganelle 参数: -1 R1 [-2 R2] -o output -F type -t threads
                    organelle_type = "embplant_mt" if kingdom == "plant" else "animal_mt"
                    if reads2_file:
                        # 双端模式
                        args = ["-1", str(reads_file), "-2", str(reads2_file),
                                "-o", str(asm_dir), "-F", organelle_type, "-t", str(threads)]
                    else:
                        # 单端模式
                        args = ["-1", str(reads_file),
                                "-o", str(asm_dir), "-F", organelle_type, "-t", str(threads)]
                    rc = self.run_tool(exe, args, cwd=asm_dir)
                    if rc.get("exit_code") == 0:
                        # 解析 GetOrganelle 输出
                        try:
                            from ...utils.parsers import parse_getorganelle_output
                            parsed = parse_getorganelle_output(asm_dir)
                            
                            if parsed['success']:
                                return {
                                    "assembler": "getorganelle",
                                    "read_type": read_type,
                                    "kingdom": inputs.get("kingdom", "animal"),
                                    "assembly_time": parsed['metrics'].get('assembly_time_seconds', 0),
                                    "assembly_file": parsed['files'].get('path_sequence', ''),
                                    "num_contigs": parsed['metrics'].get('num_sequences', 0),
                                    "total_length": parsed['metrics'].get('total_length', 0),
                                    "max_length": parsed['metrics'].get('max_length', 0),
                                    "n50": parsed['metrics'].get('total_length', 0),  # GetOrganelle 通常单序列
                                    "n90": parsed['metrics'].get('total_length', 0),
                                    "gc_content": parsed['metrics'].get('gc_content', 0),
                                    "coverage": parsed['metrics'].get('average_coverage', 0),
                                    "circular_sequences": parsed['metrics'].get('circular_sequences', 0),
                                    "target_type": parsed['metrics'].get('target_type', ''),
                                    "completeness": 0,
                                    "contamination": 0
                                }
                            else:
                                logger.warning(f"GetOrganelle parsing failed: {parsed.get('errors')}")
                        except Exception as e:
                            logger.warning(f"Failed to parse GetOrganelle output: {e}")
        except Exception as _e:
            logger.error(f"Assembly tool execution failed: {_e}")
            raise RuntimeError(
                f"Assembly failed with {assembler}. "
                f"Please ensure the tool is installed and accessible. "
                f"Error: {_e}"
            )
    
    def analyze_assembly_results(self, assembly_results: Dict[str, Any]) -> Dict[str, Any]:
        """使用 AI 分析组装结果"""
        logger.info("Analyzing assembly results with AI...")
        
        # 准备分析输入
        analysis_input = {
            "assembler": assembly_results.get("assembler", "unknown"),
            "read_type": assembly_results.get("read_type", "unknown"),
            "kingdom": assembly_results.get("kingdom", "animal"),
            "assembly_time": assembly_results.get("assembly_time", 0),
            "num_contigs": assembly_results.get("num_contigs", 0),
            "total_length": assembly_results.get("total_length", 0),
            "max_length": assembly_results.get("max_length", 0),
            "n50": assembly_results.get("n50", 0),
            "n90": assembly_results.get("n90", 0),
            "gc_content": assembly_results.get("gc_content", 0),
            "coverage": assembly_results.get("coverage", 0),
            "completeness": assembly_results.get("completeness", 0),
            "contamination": assembly_results.get("contamination", 0)
        }
        
        # 构建提示词
        prompt = ASSEMBLY_ANALYSIS_PROMPT.format(**analysis_input)
        detail_level = str((self.config or {}).get("detail_level") or os.getenv("MITO_DETAIL_LEVEL", "quick")).lower()
        if detail_level == "detailed":
            extra_guidance = "请输出完整且结构化的结果：每类要点尽量给出3-5条，包含关键阈值与推荐参数，推理要简洁但覆盖依据。"
        else:
            extra_guidance = "请保持精简：每类要点不超过2条，一句话总结，推理尽量短。"
        prompt = f"{prompt}\n\n### 输出风格要求\n{extra_guidance}"
        
        # 注入记忆与 RAG（自动探测，可用即启用；不可用时静默跳过）
        try:
            tags = ["assembly", analysis_input.get("assembler", "unknown")]
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
            "required": ["assembly_quality", "structural_analysis", "issues_found", "annotation_readiness", "reasoning"],
            "properties": {
                "assembly_quality": {"type": "object"},
                "structural_analysis": {"type": "object"},
                "issues_found": {"type": "array"},
                "optimization_recommendations": {"type": "array"},
                "polishing_strategy": {"type": "object"},
                "annotation_readiness": {"type": "object"},
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
                system=ASSEMBLY_SYSTEM_PROMPT,
                schema=schema,
                temperature=temp,
                max_tokens=max_tok
            )
            
            # 保存 AI 分析结果
            if self.workdir:
                analysis_file = self.workdir / "assembly_ai_analysis.json"
                with open(analysis_file, 'w', encoding='utf-8') as f:
                    json.dump(ai_analysis, f, indent=2, ensure_ascii=False)
            
            # 写长期记忆（Mem0），包含组装质量评估摘要与引用（若有）
            try:
                aq = ai_analysis.get("assembly_quality", {}) if isinstance(ai_analysis, dict) else {}
                summary = aq.get("summary")
                score = aq.get("overall_score")
                grade = aq.get("grade")
                self.memory_write({
                    "agent": "assembly",
                    "task_id": (self.current_task.task_id if self.current_task else "assembly"),
                    "tags": ["assembly", analysis_input.get("assembler","unknown")],
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
            basic = self._get_basic_analysis(assembly_results)
            try:
                if citations:
                    basic["references"] = citations
                aq = basic.get("assembly_quality", {}) if isinstance(basic, dict) else {}
                summary = aq.get("summary")
                score = aq.get("overall_score")
                grade = aq.get("grade")
                self.memory_write({
                    "agent": "assembly",
                    "task_id": (self.current_task.task_id if self.current_task else "assembly"),
                    "tags": ["assembly", assembly_results.get("assembler","unknown")],
                    "summary": summary or "",
                    "metrics": {"score": score, "grade": grade},
                    "citations": citations,
                })
            except Exception:
                pass
            return basic
    
    def _get_basic_analysis(self, assembly_results: Dict[str, Any]) -> Dict[str, Any]:
        """当 AI 分析失败时的基础分析"""
        n50 = assembly_results.get("n50", 0)
        num_contigs = assembly_results.get("num_contigs", 0)
        total_length = assembly_results.get("total_length", 0)
        
        # 基于规则的质量评估
        if n50 >= 15000 and num_contigs <= 2 and 16000 <= total_length <= 18000:
            grade = "A"
            score = 0.9
        elif n50 >= 10000 and num_contigs <= 5 and 15000 <= total_length <= 20000:
            grade = "B"
            score = 0.8
        elif n50 >= 5000 and num_contigs <= 10:
            grade = "C"
            score = 0.6
        else:
            grade = "D"
            score = 0.4
        
        return {
            "assembly_quality": {
                "overall_score": score,
                "grade": grade,
                "summary": f"基于规则的组装评估：N50 {n50}, 序列数 {num_contigs}, 总长度 {total_length}"
            },
            "structural_analysis": {
                "is_circular": num_contigs == 1,
                "is_complete": num_contigs <= 2 and 16000 <= total_length <= 18000,
                "fragmentation_level": "low" if num_contigs <= 3 else "high",
                "main_contigs": min(num_contigs, 5),
                "target_achieved": score >= 0.7
            },
            "issues_found": [],
            "optimization_recommendations": [
                {
                    "strategy": "序列连接",
                    "tool": "manual_curation",
                    "parameters": {},
                    "priority": "high" if num_contigs > 3 else "low",
                    "expected_improvement": "减少碎片化"
                }
            ],
            "polishing_strategy": {
                "needed": score < 0.8,
                "recommended_tools": ["pilon", "racon"],
                "iterations": 2,
                "expected_improvement": "提高序列准确性"
            },
            "annotation_readiness": {
                "ready": score >= 0.6,
                "confidence": 0.7,
                "limiting_factors": ["基于规则的简单评估"],
                "recommended_preprocessing": []
            },
            "next_steps": ["进行序列抛光", "运行注释分析"],
            "reasoning": "使用基于规则的备用分析方法"
        }