"""
质量控制智能体 - 基于 AI 的数据质量分析
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from .base_agent import BaseAgent
from .types import AgentStatus, StageResult, AgentCapability
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
    
    def execute_stage(self, inputs: Dict[str, Any]) -> StageResult:
        """执行质量控制分析阶段"""
        self.status = AgentStatus.RUNNING
        self.emit_event("stage_start", stage="qc_analysis")
        
        try:
            # 验证输入
            if not self.validate_inputs(inputs):
                raise ValueError("Input validation failed")
            
            # 执行 QC 分析
            qc_results = self.run_qc_analysis(inputs)
            
            # AI 分析结果
            ai_analysis = self.analyze_qc_results(qc_results)
            
            # 构建结果
            result = StageResult(
                status=AgentStatus.FINISHED,
                outputs={
                    "qc_results": qc_results,
                    "ai_analysis": ai_analysis,
                    "quality_score": ai_analysis.get("quality_assessment", {}).get("overall_score", 0.7)
                },
                metrics={
                    "quality_score": ai_analysis.get("quality_assessment", {}).get("overall_score", 0.7),
                    "issues_count": len(ai_analysis.get("issues_found", [])),
                    "recommendations_count": len(ai_analysis.get("recommendations", []))
                },
                logs={"qc_report": self.workdir / "qc_results.json" if self.workdir else Path("qc_results.json")}
            )
            
            self.status = AgentStatus.COMPLETED
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
        read_type = inputs.get("read_type", "illumina")
        
        logger.info(f"Running QC analysis on {reads_file}")
        
        # 这里应该调用实际的 QC 工具（FastQC, NanoPlot 等）
        # 目前返回模拟数据
        mock_results = {
            "filename": Path(reads_file).name,
            "read_type": read_type,
            "total_reads": 1000000,
            "total_bases": 150000000,
            "avg_length": 150,
            "avg_quality": 32.5,
            "q20_percent": 95.2,
            "q30_percent": 89.7,
            "gc_content": 42.3,
            "min_length": 35,
            "max_length": 151,
            "n50": 150,
            "detected_issues": [
                "轻微的质量下降在读长末端",
                "检测到少量接头序列"
            ]
        }
        
        # 保存原始 QC 结果
        if self.workdir:
            qc_file = self.workdir / "qc_results.json"
            with open(qc_file, 'w', encoding='utf-8') as f:
                json.dump(mock_results, f, indent=2, ensure_ascii=False)
        
        return mock_results
    
    def analyze_qc_results(self, qc_results: Dict[str, Any]) -> Dict[str, Any]:
        """使用 AI 分析 QC 结果"""
        logger.info("Analyzing QC results with AI...")
        
        # 准备分析输入
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
            "detected_issues": "\n".join(qc_results.get("detected_issues", []))
        }
        
        # 构建提示词
        prompt = QC_ANALYSIS_PROMPT.format(**analysis_input)
        
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
            ai_analysis = self.generate_llm_json(
                prompt=prompt,
                system=QC_SYSTEM_PROMPT,
                schema=schema,
                temperature=0.1,
                max_tokens=3000
            )
            
            # 保存 AI 分析结果
            if self.workdir:
                analysis_file = self.workdir / "qc_ai_analysis.json"
                with open(analysis_file, 'w', encoding='utf-8') as f:
                    json.dump(ai_analysis, f, indent=2, ensure_ascii=False)
            
            return ai_analysis
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            # 返回基础分析结果
            return self._get_basic_analysis(qc_results)
    
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