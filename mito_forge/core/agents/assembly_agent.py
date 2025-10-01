"""
组装智能体 - 基于 AI 的基因组组装分析
"""

import json
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
            
            self.status = AgentStatus.COMPLETED
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
        read_type = inputs.get("read_type", "illumina")
        assembler = inputs.get("assembler", "spades")
        
        logger.info(f"Running assembly with {assembler} on {reads_file}")
        
        # 这里应该调用实际的组装工具
        # 目前返回模拟数据
        mock_results = {
            "assembler": assembler,
            "read_type": read_type,
            "kingdom": inputs.get("kingdom", "animal"),
            "assembly_time": 45,
            "assembly_file": str(self.workdir / "assembly.fasta") if self.workdir else "assembly.fasta",
            "num_contigs": 3,
            "total_length": 16569,
            "max_length": 16569,
            "n50": 16569,
            "n90": 16569,
            "gc_content": 16.5,
            "coverage": 150.5,
            "completeness": 98.5,
            "contamination": 0.2
        }
        
        # 保存组装统计结果
        if self.workdir:
            stats_file = self.workdir / "assembly_stats.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(mock_results, f, indent=2, ensure_ascii=False)
        
        return mock_results
    
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
            ai_analysis = self.generate_llm_json(
                prompt=prompt,
                system=ASSEMBLY_SYSTEM_PROMPT,
                schema=schema,
                temperature=0.1,
                max_tokens=3000
            )
            
            # 保存 AI 分析结果
            if self.workdir:
                analysis_file = self.workdir / "assembly_ai_analysis.json"
                with open(analysis_file, 'w', encoding='utf-8') as f:
                    json.dump(ai_analysis, f, indent=2, ensure_ascii=False)
            
            return ai_analysis
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            # 返回基础分析结果
            return self._get_basic_analysis(assembly_results)
    
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