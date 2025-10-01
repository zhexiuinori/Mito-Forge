"""
LangGraph 节点定义
每个节点代表流水线中的一个阶段，包含具体的执行逻辑
"""
import json
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

from .state import (
    PipelineState, StageOutputs, DataType, Kingdom,
    start_stage, complete_stage, fail_stage, skip_stage
)
from ..utils.logging import get_logger

logger = get_logger(__name__)

def supervisor_node(state: PipelineState) -> PipelineState:
    """
    Supervisor Agent - 智能分析输入数据并制定最优执行策略
    
    核心职责：
    1. 深度分析输入数据特征（读长分布、质量、数据量）
    2. 智能选择最适合的工具链组合
    3. 动态调整执行参数和资源配置
    4. 制定容错和备用策略
    5. 监控整体执行进度和资源使用
    """
    logger.info(f"Supervisor Agent starting analysis for pipeline {state['pipeline_id']}")
    
    # 开始 supervisor 阶段
    start_stage(state, "supervisor")
    
    try:
        inputs = state["inputs"]
        config = state["config"]
        workdir = Path(state["workdir"])
        
        # 获取kingdom参数，优先从config中获取，然后从inputs中获取
        kingdom = config.get("kingdom", inputs.get("kingdom", "animal"))
        
        # === 第一步：深度数据分析 ===
        logger.info("Performing comprehensive data analysis...")
        data_profile = _analyze_input_data_comprehensive(inputs, workdir)
        
        # === 第二步：智能策略选择 ===
        logger.info("Selecting optimal execution strategy...")
        optimal_strategy = _select_optimal_strategy(data_profile, kingdom)
        
        # === 第三步：资源需求评估 ===
        logger.info("Estimating resource requirements...")
        resource_plan = _estimate_resource_requirements(data_profile, optimal_strategy)
        
        # === 第四步：制定执行计划 ===
        logger.info("Creating detailed execution plan...")
        execution_plan = _create_execution_plan(optimal_strategy, resource_plan, config)
        
        # === 第五步：设置监控和容错策略 ===
        logger.info("Setting up monitoring and fallback strategies...")
        monitoring_config = _setup_monitoring_strategy(data_profile, optimal_strategy)
        
        # === 更新状态配置 ===
        state["config"].update({
            # 数据分析结果
            "data_profile": data_profile,
            "detected_read_type": data_profile["read_type"].value,
            "estimated_genome_size": data_profile["estimated_genome_size"],
            "data_quality_score": data_profile["quality_score"],
            
            # 策略配置
            "selected_strategy": optimal_strategy,
            "tool_chain": optimal_strategy["tools"],
            "tool_parameters": optimal_strategy["parameters"],
            "fallback_tools": optimal_strategy["fallbacks"],
            
            # 执行计划
            "execution_plan": execution_plan,
            "stage_sequence": execution_plan["stages"],
            "conditional_stages": execution_plan["conditional_stages"],
            
            # 资源配置
            "resource_plan": resource_plan,
            "estimated_runtime": resource_plan["total_time_estimate"],
            "memory_requirements": resource_plan["memory_per_stage"],
            
            # 监控配置
            "monitoring": monitoring_config,
            "quality_thresholds": monitoring_config["thresholds"],
            "retry_strategies": monitoring_config["retry_strategies"]
        })
        
        # === 准备 Supervisor 输出 ===
        supervisor_outputs = {
            "files": {
                "analysis_report": str(workdir / "supervisor_analysis.json"),
                "execution_plan": str(workdir / "execution_plan.json"),
                "resource_plan": str(workdir / "resource_plan.json")
            },
            "metrics": {
                "confidence_score": optimal_strategy["confidence"],
                "expected_success_rate": optimal_strategy["success_probability"],
                "estimated_total_time": resource_plan["total_time_estimate"],
                "data_complexity": data_profile["complexity_score"]
            },
            "metadata": {
                "supervisor_version": "2.0.0",
                "analysis_timestamp": time.time(),
                "strategy_name": optimal_strategy["name"]
            },
            "summary": f"Selected {optimal_strategy['name']} strategy with {optimal_strategy['confidence']:.2f} confidence",
            "success": True
        }
        
        # 保存分析结果到文件
        _save_supervisor_analysis(workdir, data_profile, optimal_strategy, execution_plan, resource_plan)
        
        # 完成 supervisor 阶段
        complete_stage(state, "supervisor", supervisor_outputs)
        
        # 决定下一步路由
        next_stage = _determine_next_stage(execution_plan, state)
        state["current_stage"] = next_stage
        state["route"] = "continue"
        
        logger.info(f"Supervisor analysis completed successfully")
        logger.info(f"Strategy: {optimal_strategy['name']} (confidence: {optimal_strategy['confidence']:.2f})")
        logger.info(f"Estimated runtime: {resource_plan['total_time_estimate']:.1f} minutes")
        logger.info(f"Next stage: {next_stage}")
        
        return state
        
    except Exception as e:
        logger.error(f"Supervisor Agent failed: {e}")
        fail_stage(state, "supervisor", str(e))
        state["route"] = "terminate"
        return state

def qc_node(state: PipelineState) -> PipelineState:
    """
    质量控制节点
    
    职责：
    1. 运行 FastQC 分析
    2. 根据质量决定是否需要清理
    3. 可选的接头去除和质量修剪
    """
    logger.info("Starting QC stage")
    
    try:
        inputs = state["inputs"]
        config = state["config"]
        workdir = Path(state["workdir"])
        
        # 创建 QC 工作目录
        qc_dir = workdir / "01_qc"
        qc_dir.mkdir(parents=True, exist_ok=True)
        
        # 模拟 QC 执行（实际会调用 FastQC 等工具）
        qc_results = _run_qc_analysis(inputs, qc_dir, config)
        
        # 准备输出
        outputs = StageOutputs(
            files={
                "qc_report": str(qc_dir / "fastqc_report.html"),
                "clean_reads": qc_results.get("clean_reads", inputs["reads"])
            },
            metrics={
                "qc_score": qc_results["qc_score"],
                "total_reads": qc_results["total_reads"],
                "clean_reads": qc_results["clean_reads_count"]
            },
            metadata={
                "tool": "fastqc",
                "version": "0.12.1"
            }
        )
        
        # 更新状态
        complete_stage(state, "qc", outputs)
        state["current_stage"] = "assembly"
        state["route"] = "continue"
        
        logger.info(f"QC completed with score: {qc_results['qc_score']}")
        
        return state
        
    except Exception as e:
        logger.error(f"QC failed: {e}")
        fail_stage(state, "qc", str(e))
        state["route"] = "retry" if state["retries"].get("qc", 0) < 2 else "terminate"
        return state

def assembly_node(state: PipelineState) -> PipelineState:
    """
    组装节点
    
    职责：
    1. 根据策略选择组装工具（Flye/SPAdes/Unicycler等）
    2. 执行基因组组装
    3. 筛选线粒体候选序列
    4. 环化检测
    """
    logger.info("Starting Assembly stage")
    
    try:
        config = state["config"]
        workdir = Path(state["workdir"])
        
        # 获取 QC 后的数据
        qc_outputs = state["stage_outputs"].get("qc", {})
        reads_file = qc_outputs.get("files", {}).get("clean_reads", state["inputs"]["reads"])
        
        # 创建组装工作目录
        assembly_dir = workdir / "02_assembly"
        assembly_dir.mkdir(parents=True, exist_ok=True)
        
        # 选择组装工具
        tool_chain = config["tool_chain"]
        assembler = tool_chain["assembly"]
        
        # 执行组装
        assembly_results = _run_assembly(reads_file, assembly_dir, assembler, config)
        
        # 线粒体序列筛选
        mito_candidates = _select_mitochondrial_contigs(
            assembly_results["contigs"], 
            config.get("kingdom", "animal")
        )
        
        # 准备输出
        outputs = StageOutputs(
            files={
                "contigs": str(assembly_results["contigs"]),
                "mito_candidates": str(mito_candidates["fasta"]),
                "assembly_stats": str(assembly_dir / "stats.json")
            },
            metrics={
                "n50": assembly_results["n50"],
                "total_contigs": assembly_results["num_contigs"],
                "mito_candidates_count": mito_candidates["count"],
                "largest_contig": assembly_results["largest_contig"],
                "is_circular": mito_candidates.get("is_circular", False)
            },
            metadata={
                "tool": assembler,
                "version": assembly_results.get("version", "unknown")
            }
        )
        
        # 更新状态
        complete_stage(state, "assembly", outputs)
        state["current_stage"] = "annotation"
        state["route"] = "continue"
        
        logger.info(f"Assembly completed: {mito_candidates['count']} mitochondrial candidates found")
        
        return state
        
    except Exception as e:
        logger.error(f"Assembly failed: {e}")
        fail_stage(state, "assembly", str(e))
        
        # 决定是否重试或回退到备用工具
        if state["retries"].get("assembly", 0) < 2:
            state["route"] = "retry"
        else:
            # 尝试备用工具
            fallback_tool = _get_fallback_assembler(config["tool_chain"]["assembly"])
            if fallback_tool:
                config["tool_chain"]["assembly"] = fallback_tool
                state["route"] = "fallback"
                logger.info(f"Falling back to {fallback_tool}")
            else:
                state["route"] = "terminate"
        
        return state

def annotation_node(state: PipelineState) -> PipelineState:
    """
    注释节点
    
    职责：
    1. 对线粒体候选序列进行基因注释
    2. 生成 GFF 和功能注释
    3. 验证注释质量
    """
    logger.info("Starting Annotation stage")
    
    try:
        config = state["config"]
        workdir = Path(state["workdir"])
        
        # 获取组装结果
        assembly_outputs = state["stage_outputs"]["assembly"]
        mito_fasta = assembly_outputs["files"]["mito_candidates"]
        
        # 创建注释工作目录
        annotation_dir = workdir / "03_annotation"
        annotation_dir.mkdir(parents=True, exist_ok=True)
        
        # 执行注释
        annotation_results = _run_annotation(mito_fasta, annotation_dir, config)
        
        # 准备输出
        outputs = StageOutputs(
            files={
                "gff": str(annotation_results["gff"]),
                "genbank": str(annotation_results["genbank"]),
                "annotation_table": str(annotation_results["table"])
            },
            metrics={
                "genes_found": annotation_results["gene_count"],
                "trna_count": annotation_results["trna_count"],
                "rrna_count": annotation_results["rrna_count"],
                "annotation_completeness": annotation_results["completeness"]
            },
            metadata={
                "tool": "mitos",
                "genetic_code": config.get("genetic_code", 2)
            }
        )
        
        # 更新状态
        complete_stage(state, "annotation", outputs)
        state["current_stage"] = "report"
        state["route"] = "continue"
        
        logger.info(f"Annotation completed: {annotation_results['gene_count']} genes found")
        
        return state
        
    except Exception as e:
        logger.error(f"Annotation failed: {e}")
        fail_stage(state, "annotation", str(e))
        state["route"] = "retry" if state["retries"].get("annotation", 0) < 2 else "continue"  # 注释失败可以继续
        return state

def report_node(state: PipelineState) -> PipelineState:
    """
    报告生成节点
    
    职责：
    1. 汇总所有阶段的结果
    2. 生成 HTML 报告
    3. 创建结果摘要
    """
    logger.info("Generating final report")
    
    try:
        workdir = Path(state["workdir"])
        report_dir = workdir / "report"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成报告
        report_results = _generate_report(state, report_dir)
        
        # 标记完成
        state["done"] = True
        state["end_time"] = time.time()
        state["route"] = "END"
        
        logger.info(f"Pipeline completed successfully. Report: {report_results['html']}")
        
        return state
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        state["errors"].append(f"report: {str(e)}")
        state["done"] = True  # 即使报告失败也标记为完成
        return state

# === Supervisor Agent 核心分析函数 ===

def _analyze_input_data_comprehensive(inputs: Dict[str, Any], workdir: Path) -> Dict[str, Any]:
    """
    深度分析输入数据特征
    
    分析内容：
    1. 读长类型和分布
    2. 数据质量评估
    3. 数据量和覆盖度估算
    4. 复杂度评分
    """
    reads_path = inputs["reads"]
    
    # 基础文件信息
    file_info = _get_file_info(reads_path)
    
    # 读长类型检测
    read_type = _detect_read_type_advanced(reads_path)
    
    # 快速质量评估
    quality_metrics = _quick_quality_assessment(reads_path)
    
    # 数据量分析
    data_stats = _analyze_data_statistics(reads_path, read_type)
    
    # 复杂度评分
    complexity_score = _calculate_data_complexity(quality_metrics, data_stats, read_type)
    
    return {
        "read_type": read_type,
        "file_info": file_info,
        "quality_metrics": quality_metrics,
        "data_statistics": data_stats,
        "complexity_score": complexity_score,
        "estimated_genome_size": data_stats["estimated_genome_size"],
        "estimated_coverage": data_stats["estimated_coverage"],
        "quality_score": quality_metrics["overall_quality"],
        "analysis_timestamp": time.time()
    }

def _detect_read_type_advanced(reads_path: str) -> DataType:
    """
    高级读长类型检测
    
    检测方法：
    1. 文件名模式匹配
    2. 读长分布分析
    3. 质量分数分布
    """
    reads_path_lower = reads_path.lower()
    
    # 文件名模式检测
    if any(pattern in reads_path_lower for pattern in ["nanopore", "ont", "minion", "gridion", "promethion"]):
        return DataType.NANOPORE
    elif any(pattern in reads_path_lower for pattern in ["pacbio", "pb", "hifi", "ccs"]):
        return DataType.PACBIO_HIFI
    elif any(pattern in reads_path_lower for pattern in ["clr", "subreads"]):
        return DataType.PACBIO_CLR
    elif any(pattern in reads_path_lower for pattern in ["illumina", "hiseq", "novaseq", "miseq"]):
        return DataType.ILLUMINA
    
    # 如果文件名无法确定，进行内容分析
    try:
        read_lengths = _sample_read_lengths(reads_path, sample_size=1000)
        avg_length = sum(read_lengths) / len(read_lengths) if read_lengths else 0
        
        if avg_length > 5000:  # 长读长
            return DataType.NANOPORE  # 默认为 Nanopore
        elif avg_length > 1000:  # 中等读长
            return DataType.PACBIO_HIFI
        else:  # 短读长
            return DataType.ILLUMINA
            
    except Exception as e:
        logger.warning(f"Could not analyze read lengths: {e}")
        return DataType.ILLUMINA  # 默认值

def _select_optimal_strategy(data_profile: Dict[str, Any], kingdom: Kingdom) -> Dict[str, Any]:
    """
    基于数据特征选择最优策略
    
    策略选择考虑因素：
    1. 读长类型和质量
    2. 数据量和覆盖度
    3. 物种类型
    4. 复杂度评分
    """
    read_type = data_profile["read_type"]
    quality_score = data_profile["quality_score"]
    coverage = data_profile["estimated_coverage"]
    complexity = data_profile["complexity_score"]
    
    # 策略数据库
    strategy_matrix = {
        # (read_type, kingdom): strategy_config
        (DataType.NANOPORE, Kingdom.ANIMAL): {
            "name": "Nanopore_Animal_Optimized",
            "tools": {
                "qc": "nanoplot",
                "assembly": "flye" if coverage > 30 else "miniasm",
                "polishing": "medaka",
                "annotation": "mitos"
            },
            "parameters": {
                "flye": {"--genome-size": "16k", "--iterations": 2 if quality_score > 0.8 else 1},
                "medaka": {"--model": "r941_min_high_g360"},
                "mitos": {"--genetic-code": 2, "--kingdom": "animal"}
            },
            "fallbacks": {
                "assembly": ["miniasm", "canu"],
                "annotation": ["geseq", "cpgavas"]
            },
            "confidence": min(0.95, 0.7 + quality_score * 0.25),
            "success_probability": 0.92 if quality_score > 0.7 else 0.85
        },
        
        (DataType.ILLUMINA, Kingdom.ANIMAL): {
            "name": "Illumina_Animal_Optimized", 
            "tools": {
                "qc": "fastqc",
                "trimming": "trimmomatic" if quality_score < 0.8 else None,
                "assembly": "spades",
                "annotation": "mitos"
            },
            "parameters": {
                "spades": {"--careful": True, "-k": "21,33,55,77"},
                "trimmomatic": {"LEADING": 3, "TRAILING": 3, "SLIDINGWINDOW": "4:15"},
                "mitos": {"--genetic-code": 2, "--kingdom": "animal"}
            },
            "fallbacks": {
                "assembly": ["unicycler", "abyss"],
                "annotation": ["geseq", "cpgavas"]
            },
            "confidence": min(0.90, 0.75 + quality_score * 0.15),
            "success_probability": 0.88 if coverage > 50 else 0.82
        },
        
        (DataType.PACBIO_HIFI, Kingdom.ANIMAL): {
            "name": "PacBio_HiFi_Animal_Optimized",
            "tools": {
                "qc": "pbccs_qc",
                "assembly": "hifiasm",
                "annotation": "mitos"
            },
            "parameters": {
                "hifiasm": {"-l": 0, "--primary": True},
                "mitos": {"--genetic-code": 2, "--kingdom": "animal"}
            },
            "fallbacks": {
                "assembly": ["flye", "canu"],
                "annotation": ["geseq", "cpgavas"]
            },
            "confidence": min(0.98, 0.85 + quality_score * 0.13),
            "success_probability": 0.95 if quality_score > 0.9 else 0.90
        },
        
        # 植物策略
        (DataType.NANOPORE, Kingdom.PLANT): {
            "name": "Nanopore_Plant_Optimized",
            "tools": {
                "qc": "nanoplot",
                "assembly": "flye",
                "polishing": "medaka",
                "annotation": "geseq"
            },
            "parameters": {
                "flye": {"--genome-size": "200k", "--iterations": 3},  # 植物线粒体更大
                "geseq": {"--kingdom": "plant", "--genetic-code": 1}
            },
            "fallbacks": {
                "assembly": ["canu", "miniasm"],
                "annotation": ["cpgavas", "mitos"]
            },
            "confidence": min(0.88, 0.65 + quality_score * 0.23),
            "success_probability": 0.85 if quality_score > 0.7 else 0.78
        }
    }
    
    # 获取基础策略
    strategy_key = (read_type, kingdom)
    base_strategy = strategy_matrix.get(strategy_key)
    
    if not base_strategy:
        # 回退到默认策略
        logger.warning(f"No specific strategy for {read_type} + {kingdom}, using default")
        base_strategy = strategy_matrix[(DataType.ILLUMINA, Kingdom.ANIMAL)]
        base_strategy["confidence"] *= 0.8  # 降低置信度
    
    # 根据数据特征动态调整策略
    adjusted_strategy = _adjust_strategy_by_data(base_strategy, data_profile)
    
    return adjusted_strategy

def _adjust_strategy_by_data(strategy: Dict[str, Any], data_profile: Dict[str, Any]) -> Dict[str, Any]:
    """根据数据特征动态调整策略"""
    adjusted = strategy.copy()
    
    quality_score = data_profile["quality_score"]
    coverage = data_profile["estimated_coverage"]
    complexity = data_profile["complexity_score"]
    
    # 低质量数据调整
    if quality_score < 0.6:
        adjusted["confidence"] *= 0.8
        # 增加质控步骤
        if "trimming" not in adjusted["tools"]:
            adjusted["tools"]["trimming"] = "trimmomatic"
        # 调整组装参数
        if "spades" in adjusted["tools"]["assembly"]:
            adjusted["parameters"]["spades"]["--careful"] = True
    
    # 低覆盖度调整
    if coverage < 20:
        adjusted["confidence"] *= 0.9
        adjusted["success_probability"] *= 0.9
        # 使用更保守的组装参数
        if "flye" in adjusted["tools"]["assembly"]:
            adjusted["parameters"]["flye"]["--iterations"] = 1
    
    # 高复杂度数据调整
    if complexity > 0.8:
        adjusted["confidence"] *= 0.85
        # 增加备用工具
        if len(adjusted["fallbacks"]["assembly"]) < 3:
            adjusted["fallbacks"]["assembly"].append("canu")
    
    return adjusted

def _estimate_resource_requirements(data_profile: Dict[str, Any], strategy: Dict[str, Any]) -> Dict[str, Any]:
    """
    估算资源需求
    
    考虑因素：
    1. 数据大小
    2. 选择的工具
    3. 预期复杂度
    """
    file_size_gb = data_profile["file_info"]["size_gb"]
    read_type = data_profile["read_type"]
    coverage = data_profile["estimated_coverage"]
    
    # 基础资源需求（根据工具和数据类型）
    base_requirements = {
        DataType.NANOPORE: {
            "memory_per_gb": 4,  # GB memory per GB data
            "time_per_gb": 15,   # minutes per GB data
            "cpu_cores": 8
        },
        DataType.ILLUMINA: {
            "memory_per_gb": 6,
            "time_per_gb": 25,
            "cpu_cores": 16
        },
        DataType.PACBIO_HIFI: {
            "memory_per_gb": 3,
            "time_per_gb": 10,
            "cpu_cores": 12
        }
    }
    
    base_req = base_requirements[read_type]
    
    # 计算各阶段资源需求
    stage_requirements = {
        "qc": {
            "memory_gb": max(2, file_size_gb * 0.5),
            "time_minutes": max(5, file_size_gb * 2),
            "cpu_cores": 4
        },
        "assembly": {
            "memory_gb": max(8, file_size_gb * base_req["memory_per_gb"]),
            "time_minutes": max(30, file_size_gb * base_req["time_per_gb"]),
            "cpu_cores": base_req["cpu_cores"]
        },
        "annotation": {
            "memory_gb": max(4, file_size_gb * 1),
            "time_minutes": max(10, coverage * 0.5),
            "cpu_cores": 4
        },
        "report": {
            "memory_gb": 2,
            "time_minutes": 5,
            "cpu_cores": 2
        }
    }
    
    # 计算总需求
    total_memory = max(stage_requirements[stage]["memory_gb"] for stage in stage_requirements)
    total_time = sum(stage_requirements[stage]["time_minutes"] for stage in stage_requirements)
    
    return {
        "memory_per_stage": stage_requirements,
        "peak_memory_gb": total_memory,
        "total_time_estimate": total_time,
        "recommended_cpu_cores": base_req["cpu_cores"],
        "disk_space_gb": file_size_gb * 5,  # 5x for intermediate files
        "resource_efficiency_score": min(1.0, 10 / file_size_gb)  # 效率评分
    }

def _create_execution_plan(strategy: Dict[str, Any], resource_plan: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """创建详细的执行计划"""
    
    # 基础阶段序列
    base_stages = ["qc", "assembly", "annotation", "report"]
    
    # 根据配置调整阶段
    stages = []
    conditional_stages = {}
    
    for stage in base_stages:
        if stage == "qc" and config.get("skip_qc", False):
            conditional_stages["qc"] = "skipped_by_config"
            continue
        elif stage == "annotation" and config.get("skip_annotation", False):
            conditional_stages["annotation"] = "skipped_by_config"
            continue
        elif stage == "report" and not config.get("generate_report", True):
            conditional_stages["report"] = "skipped_by_config"
            continue
        
        stages.append(stage)
    
    # 添加条件性阶段
    if strategy["tools"].get("trimming"):
        conditional_stages["trimming"] = "if_quality_low"
    
    if strategy["tools"].get("polishing"):
        conditional_stages["polishing"] = "after_assembly"
    
    return {
        "stages": stages,
        "conditional_stages": conditional_stages,
        "stage_dependencies": {
            "assembly": ["qc"],
            "annotation": ["assembly"],
            "report": ["annotation"]
        },
        "parallel_stages": [],  # 可并行执行的阶段
        "critical_path": stages,  # 关键路径
        "estimated_checkpoints": [f"{stage}_complete" for stage in stages]
    }

def _setup_monitoring_strategy(data_profile: Dict[str, Any], strategy: Dict[str, Any]) -> Dict[str, Any]:
    """设置监控和容错策略"""
    
    quality_score = data_profile["quality_score"]
    complexity = data_profile["complexity_score"]
    
    # 质量阈值设置
    thresholds = {
        "qc_min_score": 0.6 if quality_score > 0.7 else 0.4,
        "assembly_min_n50": 10000,
        "assembly_min_contigs": 1,
        "annotation_min_genes": 10,
        "max_memory_usage": 0.9,  # 90% of available memory
        "max_runtime_multiplier": 2.0  # 2x estimated time
    }
    
    # 重试策略
    retry_strategies = {
        "qc": {
            "max_retries": 2,
            "retry_conditions": ["tool_error", "timeout"],
            "fallback_tools": ["fastqc", "nanoplot"]
        },
        "assembly": {
            "max_retries": 1,  # 组装重试成本高
            "retry_conditions": ["memory_error", "no_output"],
            "fallback_tools": strategy["fallbacks"]["assembly"]
        },
        "annotation": {
            "max_retries": 3,
            "retry_conditions": ["tool_error", "no_genes_found"],
            "fallback_tools": strategy["fallbacks"]["annotation"]
        }
    }
    
    return {
        "thresholds": thresholds,
        "retry_strategies": retry_strategies,
        "monitoring_interval": 30,  # seconds
        "resource_check_interval": 60,  # seconds
        "checkpoint_frequency": "per_stage",
        "alert_conditions": [
            "memory_usage > 95%",
            "runtime > 150% estimated",
            "disk_space < 1GB"
        ]
    }

def _determine_next_stage(execution_plan: Dict[str, Any], state: PipelineState) -> str:
    """确定下一个执行阶段"""
    stages = execution_plan["stages"]
    completed = set(state["completed_stages"])
    
    for stage in stages:
        if stage not in completed:
            return stage
    
    return "END"

def _save_supervisor_analysis(
    workdir: Path, 
    data_profile: Dict[str, Any], 
    strategy: Dict[str, Any], 
    execution_plan: Dict[str, Any], 
    resource_plan: Dict[str, Any]
) -> None:
    """保存 Supervisor 分析结果到文件"""
    
    # 确保工作目录存在
    workdir.mkdir(parents=True, exist_ok=True)
    
    # 创建分析报告
    analysis_report = {
        "supervisor_analysis": {
            "timestamp": time.time(),
            "data_profile": data_profile,
            "selected_strategy": strategy,
            "execution_plan": execution_plan,
            "resource_plan": resource_plan
        }
    }
    
    # 保存到 JSON 文件
    with open(workdir / "supervisor_analysis.json", 'w', encoding='utf-8') as f:
        json.dump(analysis_report, f, indent=2, default=str, ensure_ascii=False)
    
    with open(workdir / "execution_plan.json", 'w', encoding='utf-8') as f:
        json.dump(execution_plan, f, indent=2, ensure_ascii=False)
    
    with open(workdir / "resource_plan.json", 'w', encoding='utf-8') as f:
        json.dump(resource_plan, f, indent=2, ensure_ascii=False)

# === 数据分析辅助函数 ===

def _get_file_info(file_path: str) -> Dict[str, Any]:
    """获取文件基础信息"""
    try:
        stat = os.stat(file_path)
        return {
            "path": file_path,
            "size_bytes": stat.st_size,
            "size_gb": stat.st_size / (1024**3),
            "modified_time": stat.st_mtime,
            "exists": True
        }
    except Exception as e:
        return {
            "path": file_path,
            "size_bytes": 0,
            "size_gb": 0,
            "modified_time": 0,
            "exists": False,
            "error": str(e)
        }

def _sample_read_lengths(file_path: str, sample_size: int = 1000) -> List[int]:
    """采样读长分布"""
    lengths = []
    try:
        # 简化实现，实际会解析 FASTQ/FASTA 文件
        # 这里返回模拟数据
        if "nanopore" in file_path.lower():
            lengths = [8000 + i * 100 for i in range(sample_size)]
        elif "pacbio" in file_path.lower():
            lengths = [15000 + i * 50 for i in range(sample_size)]
        else:
            lengths = [150 + i for i in range(sample_size)]
    except Exception as e:
        logger.warning(f"Could not sample read lengths: {e}")
    
    return lengths[:sample_size]

def _quick_quality_assessment(file_path: str) -> Dict[str, Any]:
    """快速质量评估"""
    # 简化实现，实际会运行 FastQC 或类似工具
    return {
        "overall_quality": 0.85,  # 模拟质量分数
        "avg_phred_score": 28,
        "gc_content": 0.42,
        "n_content": 0.01,
        "sequence_length_distribution": "normal",
        "adapter_contamination": 0.02
    }

def _analyze_data_statistics(file_path: str, read_type: DataType) -> Dict[str, Any]:
    """分析数据统计信息"""
    file_info = _get_file_info(file_path)
    
    # 根据读长类型估算
    if read_type == DataType.NANOPORE:
        avg_read_length = 8000
        reads_per_gb = 125000
    elif read_type == DataType.PACBIO_HIFI:
        avg_read_length = 15000
        reads_per_gb = 67000
    else:  # Illumina
        avg_read_length = 150
        reads_per_gb = 6700000
    
    estimated_reads = int(file_info["size_gb"] * reads_per_gb)
    total_bases = estimated_reads * avg_read_length
    
    # 线粒体基因组大小估算（动物：16kb，植物：200kb）
    mito_genome_size = 16000  # 默认动物
    estimated_coverage = total_bases / mito_genome_size
    
    return {
        "estimated_reads": estimated_reads,
        "avg_read_length": avg_read_length,
        "total_bases": total_bases,
        "estimated_genome_size": mito_genome_size,
        "estimated_coverage": estimated_coverage,
        "data_density": file_info["size_gb"] / max(1, estimated_reads / 1000000)
    }

def _calculate_data_complexity(quality_metrics: Dict[str, Any], data_stats: Dict[str, Any], read_type: DataType) -> float:
    """计算数据复杂度评分 (0-1)"""
    
    # 质量因子
    quality_factor = quality_metrics["overall_quality"]
    
    # 覆盖度因子
    coverage = data_stats["estimated_coverage"]
    coverage_factor = min(1.0, coverage / 50)  # 50x 为理想覆盖度
    
    # 读长类型因子
    type_factors = {
        DataType.PACBIO_HIFI: 0.2,  # 最简单
        DataType.ILLUMINA: 0.5,     # 中等
        DataType.NANOPORE: 0.7,     # 较复杂
        DataType.PACBIO_CLR: 0.8    # 最复杂
    }
    type_factor = type_factors.get(read_type, 0.5)
    
    # 数据量因子
    size_gb = data_stats.get("data_density", 1)
    size_factor = min(1.0, size_gb / 10)  # 10GB 为复杂阈值
    
    # 综合复杂度 (越高越复杂)
    complexity = (
        (1 - quality_factor) * 0.3 +
        (1 - coverage_factor) * 0.2 +
        type_factor * 0.3 +
        size_factor * 0.2
    )
    
    return min(1.0, max(0.0, complexity))

# === 兼容性函数 ===

def _analyze_read_type(inputs: Dict[str, Any]) -> str:
    """分析读长类型（兼容性函数）"""
    return _detect_read_type_advanced(inputs.get("reads", "")).value

def _select_strategy(read_type: str, kingdom: str) -> Dict[str, Any]:
    """选择执行策略（兼容性函数）"""
    # 转换为新的数据类型
    try:
        read_type_enum = DataType(read_type)
        kingdom_enum = Kingdom(kingdom)
    except ValueError:
        read_type_enum = DataType.ILLUMINA
        kingdom_enum = Kingdom.ANIMAL
    
    # 创建简化的数据配置文件
    mock_profile = {
        "read_type": read_type_enum,
        "quality_score": 0.8,
        "estimated_coverage": 50,
        "complexity_score": 0.5
    }
    
    return _select_optimal_strategy(mock_profile, kingdom_enum)

def _run_qc_analysis(inputs: Dict[str, Any], qc_dir: Path, config: Dict[str, Any]) -> Dict[str, Any]:
    """执行 QC 分析（模拟）"""
    # 实际实现会调用 FastQC 等工具
    return {
        "qc_score": 0.92,
        "total_reads": 50000,
        "clean_reads_count": 48500,
        "clean_reads": str(qc_dir / "clean_reads.fastq")
    }

def _run_assembly(reads_file: str, assembly_dir: Path, assembler: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """执行基因组组装（模拟）"""
    # 实际实现会调用 Flye/SPAdes 等工具
    contigs_file = assembly_dir / "contigs.fasta"
    contigs_file.write_text(">contig_1\nATCGATCGATCG...\n")  # 模拟序列
    
    return {
        "contigs": str(contigs_file),
        "n50": 16800,
        "num_contigs": 3,
        "largest_contig": 16800,
        "version": "2.9.1"
    }

def _select_mitochondrial_contigs(contigs_file: str, kingdom: str) -> Dict[str, Any]:
    """筛选线粒体序列（模拟）"""
    # 实际实现会基于长度、覆盖度或 BLAST 筛选
    mito_file = Path(contigs_file).parent / "mitochondrial_candidates.fasta"
    mito_file.write_text(">mito_candidate_1\nATCGATCGATCG...\n")
    
    return {
        "fasta": str(mito_file),
        "count": 1,
        "is_circular": True
    }

def _run_annotation(mito_fasta: str, annotation_dir: Path, config: Dict[str, Any]) -> Dict[str, Any]:
    """执行基因注释（模拟）"""
    # 实际实现会调用 MITOS 等工具
    gff_file = annotation_dir / "annotation.gff"
    gff_file.write_text("##gff-version 3\n# Mock annotation\n")
    
    return {
        "gff": str(gff_file),
        "genbank": str(annotation_dir / "annotation.gb"),
        "table": str(annotation_dir / "genes.tsv"),
        "gene_count": 37,
        "trna_count": 22,
        "rrna_count": 2,
        "completeness": 0.95
    }

def _generate_report(state: PipelineState, report_dir: Path) -> Dict[str, Any]:
    """生成最终报告（模拟）"""
    # 实际实现会生成 HTML 报告
    html_file = report_dir / "pipeline_report.html"
    html_file.write_text("<html><body><h1>Mitochondrial Assembly Report</h1></body></html>")
    
    summary_file = report_dir / "summary.json"
    summary_file.write_text(json.dumps(state, indent=2, default=str))
    
    return {
        "html": str(html_file),
        "summary": str(summary_file)
    }

def _get_fallback_assembler(current_assembler: str) -> str:
    """获取备用组装工具"""
    fallbacks = {
        "flye": "spades",
        "spades": "unicycler",
        "unicycler": "flye"
    }
    return fallbacks.get(current_assembler)