"""
注释智能体 - 基于 AI 的基因注释分析
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from .base_agent import BaseAgent
from .types import AgentStatus, StageResult, AgentCapability
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
    
    def execute_stage(self, inputs: Dict[str, Any]) -> StageResult:
        """执行基因注释阶段"""
        self.status = AgentStatus.RUNNING
        self.emit_event("stage_start", stage="annotation")
        
        try:
            # 验证输入
            if not self.validate_inputs(inputs):
                raise ValueError("Input validation failed")
            
            # 执行注释
            annotation_results = self.run_annotation(inputs)
            
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
                exe = find_tool("runmitos.py") or find_tool("mitos")
                if exe:
                    # MITOS 参数: --input assembly.fasta --code 2 --outdir output
                    genetic_code = 2 if kingdom == "animal" else 1
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
    
    def analyze_annotation_results(self, annotation_results: Dict[str, Any]) -> Dict[str, Any]:
        """使用 AI 分析注释结果"""
        logger.info("Analyzing annotation results with AI...")
        
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