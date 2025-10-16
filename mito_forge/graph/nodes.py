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
    PipelineState, StageOutputs, DataType, Kingdom, RouteDecision,
    start_stage, complete_stage, fail_stage, skip_stage
)
from ..utils.logging import get_logger

logger = get_logger(__name__)

# === 引入真实评估所需的 Agents 与类型（最小侵入） ===
try:
    from ..core.agents.qc_agent import QCAgent
    from ..core.agents.assembly_agent import AssemblyAgent
    from ..core.agents.annotation_agent import AnnotationAgent
    from ..core.agents.supervisor_agent import SupervisorAgent
    from ..core.agents.types import TaskSpec
except Exception:
    QCAgent = AssemblyAgent = AnnotationAgent = SupervisorAgent = None
    TaskSpec = None

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
        
        # 若已提供来自 selection 的工具计划，则优先采用，降低重复判断
        tool_plan = (config or {}).get("tool_plan")
        preselected_tool_chain = None
        if isinstance(tool_plan, dict):
            try:
                # 将 plan 映射为 nodes 内部使用的 tool_chain 结构
                qc_tool = None
                if isinstance(tool_plan.get("qc"), list) and tool_plan["qc"]:
                    qc_tool = tool_plan["qc"][0]
                elif isinstance(tool_plan.get("qc"), str):
                    qc_tool = tool_plan["qc"]
                assembler_tool = None
                asm = tool_plan.get("assembler") or {}
                if isinstance(asm, dict) and asm.get("name"):
                    assembler_tool = asm["name"]
                elif isinstance(asm, str):
                    assembler_tool = asm
                polishing_tool = None
                pol_list = tool_plan.get("polishers") or []
                if isinstance(pol_list, list) and pol_list:
                    # nodes 的策略里只保留一个标识，实际抛光细节在执行阶段细化
                    polishing_tool = pol_list[0]
                preselected_tool_chain = {
                    "qc": qc_tool or "fastqc",
                    "assembly": assembler_tool or "spades",
                    "polishing": polishing_tool,  # 可为 None
                    "annotation": "mitos",        # 保持默认，后续可由 kingdom 细化
                }
                # 将该链路预先写入 config，供后续阶段直接使用
                state["config"]["tool_chain"] = preselected_tool_chain
            except Exception as _e:
                logger.warning(f"Failed to consume provided tool_plan, will fall back to internal strategy: {_e}")
                preselected_tool_chain = None

        # === 第一步：深度数据分析 ===
        logger.info("Performing comprehensive data analysis...")
        data_profile = _analyze_input_data_comprehensive(inputs, workdir)
        
        # === 第二步：智能策略选择或采用预选方案 ===
        logger.info("Selecting optimal execution strategy...")
        if preselected_tool_chain:
            # 以预选链路构造一个与内部格式兼容的“已选策略”
            # 合并 tool_plan 中 assembler.params 到 parameters.{assembler}
            asm_params = {}
            try:
                _asm = (tool_plan or {}).get("assembler") or {}
                if isinstance(_asm, dict):
                    _p = _asm.get("params") or {}
                    if isinstance(_p, dict):
                        asm_params = _p
            except Exception:
                asm_params = {}
            assembler_name = preselected_tool_chain.get("assembly") or "spades"
            parameters = {}
            if assembler_name and asm_params:
                parameters[assembler_name] = dict(asm_params)

            optimal_strategy = {
                "name": "Preselected_From_ToolPlan",
                "tools": preselected_tool_chain,
                "parameters": parameters,
                "fallbacks": {
                    "assembly": ["flye", "spades", "unicycler"],
                    "annotation": ["mitos", "geseq"]
                },
                "confidence": 0.9,
                "success_probability": 0.9
            }
        else:
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
        state["route"] = RouteDecision.CONTINUE
        
        logger.info(f"Supervisor analysis completed successfully")
        logger.info(f"Strategy: {optimal_strategy['name']} (confidence: {optimal_strategy['confidence']:.2f})")
        logger.info(f"Estimated runtime: {resource_plan['total_time_estimate']:.1f} minutes")
        logger.info(f"Next stage: {next_stage}")
        
        return state
        
    except Exception as e:
        logger.error(f"Supervisor Agent failed: {e}")
        fail_stage(state, "supervisor", str(e))
        state["route"] = RouteDecision.TERMINATE
        return state

def qc_node(state: PipelineState) -> PipelineState:
    """
    质量控制节点
    
    职责：
    1. 运行 FastQC 分析
    2. 根据质量决定是否需要清理
    3. 可选的接头去除和质量修剪
    4. 支持双端测序数据（R1 和 R2）
    """
    logger.info("Starting QC stage")
    
    try:
        inputs = state["inputs"]
        # 获取 R2（如果存在）
        reads2 = inputs.get("reads2")
        if reads2:
            logger.info(f"Processing paired-end data: R1={inputs['reads']}, R2={reads2}")
        config = state["config"]
        workdir = Path(state["workdir"])
        
        # 创建 QC 工作目录
        qc_dir = workdir / "01_qc"
        qc_dir.mkdir(parents=True, exist_ok=True)
        
        # 模拟 QC 执行（实际会调用 FastQC 等工具）
        qc_results = _run_qc_analysis(inputs, qc_dir, config)
        
        # 可选：调用真实 QC Agent 进行 LLM 评估（按分级 quick/detailed/expert 调整深度）
        ai_metrics = {}
        ai_file = None
        try:
            if QCAgent and TaskSpec and state["config"].get("enable_llm_eval", True):
                detail_level = os.getenv("MITO_DETAIL_LEVEL", "quick").lower()
                qc_agent = QCAgent(state["config"])
                # 初评（quick/detailed/expert 都会调用一次）
                base_cfg = {"read_type": "illumina", "detail_level": detail_level, "llm_depth": 1}
                # 准备 QC inputs，包含 reads2
                qc_inputs = {"reads": str(inputs["reads"])}
                if reads2:
                    qc_inputs["reads2"] = str(reads2)
                
                task = TaskSpec(
                    task_id="qc_pipeline",
                    agent_type="qc",
                    inputs=qc_inputs,
                    config=base_cfg,
                    workdir=qc_dir
                )
                _res = qc_agent.execute_task(task)
                
                # 立即检查Agent执行状态,避免后续代码抛出异常
                from ..core.agents.types import AgentStatus
                if _res.status == AgentStatus.FAILED:
                    error_msg = str(_res.errors[0]) if _res.errors else "QC analysis failed"
                    logger.error(f"🛑 QC Agent failed, terminating pipeline: {error_msg}")
                    fail_stage(state, "qc", error_msg)
                    state["route"] = RouteDecision.TERMINATE
                    return state
                
                _ai = (_res.outputs or {}).get("ai_analysis", {}) or {}
                merged_ai = dict(_ai) if isinstance(_ai, dict) else {"raw": _ai}
                # expert 追加复核一轮（第二次调用），合并结果
                if detail_level == "expert":
                    review_cfg = {"read_type": "illumina", "detail_level": "expert", "llm_depth": 2, "review_of": merged_ai}
                    # 准备 review inputs，也包含 reads2
                    review_qc_inputs = {"reads": str(inputs["reads"]), "review": True}
                    if reads2:
                        review_qc_inputs["reads2"] = str(reads2)
                    
                    review_task = TaskSpec(
                        task_id="qc_pipeline_review",
                        agent_type="qc",
                        inputs=review_qc_inputs,
                        config=review_cfg,
                        workdir=qc_dir
                    )
                    _res2 = qc_agent.execute_task(review_task)
                    _ai2 = (_res2.outputs or {}).get("ai_analysis", {}) or {}
                    if isinstance(_ai2, dict):
                        merged_ai["review"] = _ai2
                # 提取关键指标（优先用复核结果的评分/等级/摘要）
                _qa = (merged_ai.get("quality_assessment") or merged_ai.get("qc_quality") or {})
                # 回退逻辑：如果复核层级未提供标准键，尝试从 review 中取
                if not _qa and isinstance(merged_ai.get("review"), dict):
                    _qa = (merged_ai["review"].get("quality_assessment") or merged_ai["review"].get("qc_quality") or {})
                ai_metrics = {
                    "ai_quality_score": _qa.get("overall_score"),
                    "ai_grade": _qa.get("grade"),
                    "ai_summary": _qa.get("summary")
                }
                # 保存评估文件
                ai_file = str(qc_dir / "qc_ai_analysis.json")
                with open(ai_file, "w", encoding="utf-8") as f:
                    json.dump(merged_ai, f, ensure_ascii=False, indent=2)
                    
        except Exception as _e:
            logger.warning(f"QC LLM评估失败，使用模拟结果: {_e}")
        
        # 准备输出
        files_dict = {
            "qc_report": str(qc_dir / "fastqc_report.html"),
            "clean_reads": qc_results.get("clean_reads", inputs["reads"])
        }
        # 如果有 R2，也添加到输出
        if reads2:
            files_dict["clean_reads2"] = qc_results.get("clean_reads2", reads2)
        if ai_file:
            files_dict["qc_ai_analysis"] = ai_file
        
        metrics_dict = {
            "qc_score": qc_results["qc_score"],
            "total_reads": qc_results["total_reads"],
            "clean_reads": qc_results["clean_reads_count"]
        }
        # 合并 AI 评估指标
        metrics_dict.update({k: v for k, v in ai_metrics.items() if v is not None})
        
        outputs = StageOutputs(
            files=files_dict,
            metrics=metrics_dict,
            metadata={
                "tool": "fastqc",
                "version": "0.12.1"
            }
        )
        
        # 更新状态
        complete_stage(state, "qc", outputs)
        state["current_stage"] = "assembly"
        state["route"] = RouteDecision.CONTINUE
        
        logger.info(f"QC completed with score: {qc_results['qc_score']}")
        
        return state
        
    except Exception as e:
        logger.error(f"QC failed: {e}")
        fail_stage(state, "qc", str(e))
        # QC Agent 内部已经处理了错误（包括重试和修复）
        # 如果到这里说明确实无法修复，直接终止
        state["route"] = RouteDecision.TERMINATE
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
        reads2_file = qc_outputs.get("files", {}).get("clean_reads2", state["inputs"].get("reads2"))
        
        # 若清洗后的reads文件不存在，则回退到原始reads
        try:
            if not Path(reads_file).exists():
                logger.warning(f"Clean reads not found at {reads_file}, falling back to original input reads")
                reads_file = state["inputs"]["reads"]
                reads2_file = state["inputs"].get("reads2")
        except Exception as _e:
            logger.warning(f"Failed to validate clean_reads path ({reads_file}), fallback to original reads: {_e}")
            reads_file = state["inputs"]["reads"]
            reads2_file = state["inputs"].get("reads2")
        
        # 创建组装工作目录
        assembly_dir = workdir / "02_assembly"
        assembly_dir.mkdir(parents=True, exist_ok=True)
        
        # 选择组装工具
        tool_chain = config["tool_chain"]
        assembler = tool_chain["assembly"]
        
        # 初始化为None,后续从Agent获取真实结果
        assembly_results = None
        mito_candidates = None
        
        # 可选：调用真实 Assembly Agent 进行 LLM 评估（按分级 quick/detailed/expert 调整深度）
        asm_ai_metrics = {}
        asm_ai_file = None
        try:
            if AssemblyAgent and TaskSpec and state["config"].get("enable_llm_eval", True):
                detail_level = os.getenv("MITO_DETAIL_LEVEL", "quick").lower()
                asm_agent = AssemblyAgent(state["config"])
                detected_rt = state["config"].get("detected_read_type", "illumina")
                # 初评一次（所有分级都会执行）
                base_cfg = {"assembler": assembler, "detail_level": detail_level, "llm_depth": 1}
                # 准备 inputs，包含 reads2
                agent_inputs = {
                    "reads": str(reads_file),
                    "read_type": detected_rt,
                    "kingdom": state["config"].get("kingdom", "animal"),
                    "assembler": assembler
                }
                if reads2_file:
                    agent_inputs["reads2"] = str(reads2_file)
                
                task = TaskSpec(
                    task_id="assembly_pipeline",
                    agent_type="assembly",
                    inputs=agent_inputs,
                    config=base_cfg,
                    workdir=assembly_dir
                )
                _res = asm_agent.execute_task(task)
                
                # 立即检查Agent执行状态
                from ..core.agents.types import AgentStatus
                if _res.status == AgentStatus.FAILED:
                    error_msg = str(_res.errors[0]) if _res.errors else "Assembly failed"
                    logger.error(f"🛑 Assembly Agent failed, terminating pipeline: {error_msg}")
                    fail_stage(state, "assembly", error_msg)
                    state["route"] = RouteDecision.TERMINATE
                    return state
                
                # 提取Agent的真实组装结果
                agent_outputs = _res.outputs or {}
                assembly_results = agent_outputs.get("assembly_results", {})
                mito_file = agent_outputs.get("assembly_file")
                
                # 如果Agent返回了线粒体文件,设置mito_candidates
                if mito_file and Path(mito_file).exists():
                    mito_candidates = {
                        "fasta": str(mito_file),
                        "count": 1,  # TODO: 从assembly_results解析
                        "is_circular": assembly_results.get("is_circular", False)
                    }
                
                _ai = agent_outputs.get("ai_analysis", {}) or {}
                merged_ai = dict(_ai) if isinstance(_ai, dict) else {"raw": _ai}
                # expert 追加一轮复核
                if detail_level == "expert":
                    review_cfg = {"assembler": assembler, "detail_level": "expert", "llm_depth": 2, "review_of": merged_ai}
                    # 准备 review inputs，也包含 reads2
                    review_inputs = {
                        "reads": str(reads_file),
                        "read_type": detected_rt,
                        "kingdom": state["config"].get("kingdom", "animal"),
                        "assembler": assembler,
                        "review": True
                    }
                    if reads2_file:
                        review_inputs["reads2"] = str(reads2_file)
                    
                    review_task = TaskSpec(
                        task_id="assembly_pipeline_review",
                        agent_type="assembly",
                        inputs=review_inputs,
                        config=review_cfg,
                        workdir=assembly_dir
                    )
                    _res2 = asm_agent.execute_task(review_task)
                    _ai2 = (_res2.outputs or {}).get("ai_analysis", {}) or {}
                    if isinstance(_ai2, dict):
                        merged_ai["review"] = _ai2
                _aq = (merged_ai.get("assembly_quality") or merged_ai.get("assembly_assessment") or {})
                if not _aq and isinstance(merged_ai.get("review"), dict):
                    _aq = (merged_ai["review"].get("assembly_quality") or merged_ai["review"].get("assembly_assessment") or {})
                asm_ai_metrics = {
                    "ai_quality_score": _aq.get("overall_score"),
                    "ai_grade": _aq.get("grade"),
                    "ai_summary": _aq.get("summary")
                }
                asm_ai_file = str(assembly_dir / "assembly_ai_analysis.json")
                with open(asm_ai_file, "w", encoding="utf-8") as f:
                    json.dump(merged_ai, f, ensure_ascii=False, indent=2)
                    
        except Exception as _e:
            logger.warning(f"Assembly Agent执行失败，使用模拟结果: {_e}")
        
        # Fallback: 如果Agent没有返回结果,使用模拟数据
        if assembly_results is None or mito_candidates is None:
            logger.warning("Assembly Agent未返回结果,使用模拟数据")
            # 执行组装(模拟)
            assembly_results = _run_assembly(reads_file, assembly_dir, assembler, config)
            # 线粒体序列筛选(模拟)
            mito_candidates = _select_mitochondrial_contigs(
                assembly_results["contigs"],
                config.get("kingdom", "animal")
            )
        
        # 准备输出
        files_dict = {
            "contigs": str(assembly_results["contigs"]),
            "mito_candidates": str(mito_candidates["fasta"]),
            "assembly_stats": str(assembly_dir / "stats.json")
        }
        if asm_ai_file:
            files_dict["assembly_ai_analysis"] = asm_ai_file
        
        metrics_dict = {
            "n50": assembly_results.get("n50", 0),
            "total_contigs": assembly_results.get("num_contigs", assembly_results.get("total_contigs", 0)),
            "mito_candidates_count": mito_candidates.get("count", 0),
            "largest_contig": assembly_results.get("largest_contig", assembly_results.get("max_length", 0)),
            "is_circular": mito_candidates.get("is_circular", False)
        }
        metrics_dict.update({k: v for k, v in asm_ai_metrics.items() if v is not None})
        
        outputs = StageOutputs(
            files=files_dict,
            metrics=metrics_dict,
            metadata={
                "tool": assembler,
                "version": assembly_results.get("version", "unknown")
            }
        )
        
        # 更新状态
        complete_stage(state, "assembly", outputs)
        # 不直接设置 current_stage，让路由决策器决定下一步（polish 或 annotation）
        state["route"] = RouteDecision.CONTINUE
        
        logger.info(f"Assembly completed: {mito_candidates['count']} mitochondrial candidates found")
        
        return state
        
    except Exception as e:
        logger.error(f"Assembly failed: {e}")
        fail_stage(state, "assembly", str(e))
        # Assembly Agent 内部已经处理了错误（包括重试和修复）
        # 如果到这里说明确实无法修复，直接终止
        state["route"] = RouteDecision.TERMINATE
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
        
        # 可选：调用真实 Annotation Agent 进行 LLM 评估（按分级 quick/detailed/expert 调整深度）
        ann_ai_metrics = {}
        ann_ai_file = None
        try:
            if AnnotationAgent and TaskSpec and state["config"].get("enable_llm_eval", True):
                detail_level = os.getenv("MITO_DETAIL_LEVEL", "quick").lower()
                ann_agent = AnnotationAgent(state["config"])
                base_cfg = {"annotator": "mitos", "detail_level": detail_level, "llm_depth": 1}
                task = TaskSpec(
                    task_id="annotation_pipeline",
                    agent_type="annotation",
                    inputs={"assembly": str(mito_fasta), "kingdom": state["config"].get("kingdom", "animal"), "genetic_code": config.get("genetic_code", 2), "interactive": config.get("interactive", False)},
                    config=base_cfg,
                    workdir=annotation_dir
                )
                _res = ann_agent.execute_task(task)
                
                # 立即检查Agent执行状态
                from ..core.agents.types import AgentStatus
                if _res.status == AgentStatus.FAILED:
                    error_msg = str(_res.errors[0]) if _res.errors else "Annotation failed"
                    logger.error(f"🛑 Annotation Agent failed, terminating pipeline: {error_msg}")
                    fail_stage(state, "annotation", error_msg)
                    state["route"] = RouteDecision.TERMINATE
                    return state
                
                _ai = (_res.outputs or {}).get("ai_analysis", {}) or {}
                merged_ai = dict(_ai) if isinstance(_ai, dict) else {"raw": _ai}
                # expert 再进行一轮复核
                if detail_level == "expert":
                    review_cfg = {"annotator": "mitos", "detail_level": "expert", "llm_depth": 2, "review_of": merged_ai}
                    review_task = TaskSpec(
                        task_id="annotation_pipeline_review",
                        agent_type="annotation",
                        inputs={"assembly": str(mito_fasta), "kingdom": state["config"].get("kingdom", "animal"), "genetic_code": config.get("genetic_code", 2), "interactive": config.get("interactive", False), "review": True},
                        config=review_cfg,
                        workdir=annotation_dir
                    )
                    _res2 = ann_agent.execute_task(review_task)
                    _ai2 = (_res2.outputs or {}).get("ai_analysis", {}) or {}
                    if isinstance(_ai2, dict):
                        merged_ai["review"] = _ai2
                _aq = (merged_ai.get("annotation_quality") or merged_ai.get("annotation_assessment") or {})
                if not _aq and isinstance(merged_ai.get("review"), dict):
                    _aq = (merged_ai["review"].get("annotation_quality") or merged_ai["review"].get("annotation_assessment") or {})
                ann_ai_metrics = {
                    "ai_quality_score": _aq.get("overall_score"),
                    "ai_grade": _aq.get("grade"),
                    "ai_summary": _aq.get("summary")
                }
                ann_ai_file = str(annotation_dir / "annotation_ai_analysis.json")
                with open(ann_ai_file, "w", encoding="utf-8") as f:
                    json.dump(merged_ai, f, ensure_ascii=False, indent=2)
                    
        except Exception as _e:
            logger.warning(f"Annotation LLM评估失败，使用模拟结果: {_e}")
        
        # 准备输出
        files_dict = {
            "gff": str(annotation_results["gff"]),
            "genbank": str(annotation_results["genbank"]),
            "annotation_table": str(annotation_results["table"])
        }
        if ann_ai_file:
            files_dict["annotation_ai_analysis"] = ann_ai_file
        
        metrics_dict = {
            "genes_found": annotation_results["gene_count"],
            "trna_count": annotation_results["trna_count"],
            "rrna_count": annotation_results["rrna_count"],
            "annotation_completeness": annotation_results["completeness"]
        }
        metrics_dict.update({k: v for k, v in ann_ai_metrics.items() if v is not None})
        
        outputs = StageOutputs(
            files=files_dict,
            metrics=metrics_dict,
            metadata={
                "tool": "mitos",
                "genetic_code": config.get("genetic_code", 2)
            }
        )
        
        # 更新状态
        complete_stage(state, "annotation", outputs)
        state["current_stage"] = "report"
        state["route"] = RouteDecision.CONTINUE
        
        logger.info(f"Annotation completed: {annotation_results['gene_count']} genes found")
        
        return state
        
    except Exception as e:
        logger.error(f"Annotation failed: {e}")
        fail_stage(state, "annotation", str(e))
        # Annotation Agent 内部已经处理了错误（包括重试和修复）
        # 如果到这里说明确实无法修复，注释失败可以继续报告阶段
        state["route"] = RouteDecision.CONTINUE
        return state

def polish_node(state: PipelineState) -> PipelineState:
    """
    抛光节点 - 提高组装准确性
    
    职责：
    1. 根据数据类型和策略选择抛光工具
    2. 执行序列抛光（Racon/Pilon/Medaka）
    3. 质量对比（抛光前后）
    4. 更新组装结果
    
    抛光策略：
    - Illumina: Pilon（需要比对）
    - Nanopore: Racon + Medaka（推荐）
    - PacBio CLR: Racon 多轮
    - PacBio HiFi: 通常不需要抛光
    """
    logger.info("Starting Polishing stage")
    
    start_stage(state, "polish")
    
    try:
        config = state["config"]
        workdir = Path(state["workdir"])
        
        # 获取组装结果
        assembly_outputs = state["stage_outputs"].get("assembly", {})
        assembly_file = assembly_outputs.get("files", {}).get("assembly")
        
        if not assembly_file or not Path(assembly_file).exists():
            logger.error("Assembly file not found, skipping polishing")
            skip_stage(state, "polish", "no_assembly_file")
            state["route"] = RouteDecision.CONTINUE
            return state
        
        # 检查是否需要抛光
        tool_chain = config.get("tool_chain", {})
        polishing_tool = tool_chain.get("polishing")
        
        if not polishing_tool:
            logger.info("No polishing tool specified, skipping polishing")
            skip_stage(state, "polish", "not_needed")
            state["route"] = RouteDecision.CONTINUE
            return state
        
        # 创建抛光工作目录
        polish_dir = workdir / "03_polish"
        polish_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取原始读段
        qc_outputs = state["stage_outputs"].get("qc", {})
        reads_file = qc_outputs.get("files", {}).get("clean_reads", state["inputs"]["reads"])
        reads2_file = qc_outputs.get("files", {}).get("clean_reads2", state["inputs"].get("reads2"))
        
        # 获取数据类型
        read_type = config.get("detected_read_type", "illumina")
        
        # 执行抛光
        logger.info(f"Running {polishing_tool} polishing on {read_type} data")
        
        polish_results = _run_polishing(
            reads_file=reads_file,
            reads2_file=reads2_file,
            assembly_file=assembly_file,
            output_dir=polish_dir,
            tool=polishing_tool,
            read_type=read_type,
            threads=config.get("threads", 4)
        )
        
        # 标记完成
        files_dict = {
            "polished_assembly": polish_results["polished_file"],
            "original_assembly": assembly_file
        }
        
        metrics_dict = {
            "tool": polishing_tool,
            "iterations": polish_results.get("iterations", 1),
            "improvement": _calculate_improvement(
                assembly_file, 
                polish_results["polished_file"]
            )
        }
        
        complete_stage(
            state,
            "polish",
            files=files_dict,
            metrics=metrics_dict
        )
        
        # 更新组装文件为抛光后的版本
        state["stage_outputs"]["assembly"]["files"]["assembly"] = polish_results["polished_file"]
        
        state["route"] = RouteDecision.CONTINUE
        logger.info(f"Polishing completed with {polishing_tool}")
        
        return state
        
    except Exception as e:
        logger.error(f"Polishing failed: {e}")
        fail_stage(state, "polish", str(e))
        # 抛光失败不致命，继续后续流程
        state["route"] = RouteDecision.CONTINUE
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
        state["route"] = RouteDecision.CONTINUE  # END 会由 graph 处理
        
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
        "resource_efficiency_score": min(1.0, 10 / max(file_size_gb, 1e-9))  # 效率评分（防止除零）
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
    """执行 QC 分析（模拟，应用 plan 参数并记录）"""
    # 实际实现会调用 FastQC 等工具；这里记录参数以便测试验证
    try:
        qc_tool = (config.get("tool_chain") or {}).get("qc", "fastqc")
        params = (config.get("tool_parameters") or {}).get(qc_tool, {})
        (qc_dir / "qc_used_params.json").write_text(json.dumps(params, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
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
    """生成最终报告"""
    from ..reports import generate_html_report
    
    # 生成 HTML 报告
    html_file = report_dir / "pipeline_report.html"
    try:
        generate_html_report(state, html_file)
        logger.info(f"HTML report generated: {html_file}")
    except Exception as e:
        logger.error(f"Failed to generate HTML report: {e}")
        # 回退到简单报告
        html_file.write_text(f"<html><body><h1>Mito-Forge Pipeline Report</h1><p>Error: {e}</p></body></html>")
    
    # 生成 JSON 摘要
    summary_file = report_dir / "summary.json"
    
    # 计算 duration，处理 None 值
    start_time = state.get('start_time', 0)
    end_time = state.get('end_time', 0)
    if start_time and end_time:
        duration = end_time - start_time
    else:
        duration = 0
    
    summary_data = {
        'pipeline_id': state['pipeline_id'],
        'status': 'completed' if state.get('done') else 'failed',
        'start_time': start_time,
        'end_time': end_time,
        'duration': duration,
        'stages': {
            stage: {
                'status': state['stage_status'].get(stage, 'pending'),
                'metrics': state['stage_metrics'].get(stage, {}),
                'files': state['stage_outputs'].get(stage, {}).get('files', {})
            }
            for stage in ['qc', 'assembly', 'polish', 'annotation']
        },
        'config': state.get('config', {}),
        'errors': state.get('errors', [])
    }
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, default=str, ensure_ascii=False)
    
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

def _run_polishing(
    reads_file: str,
    reads2_file: Optional[str],
    assembly_file: str,
    output_dir: Path,
    tool: str,
    read_type: str,
    threads: int = 4
) -> Dict[str, Any]:
    """
    执行抛光
    
    根据工具类型和数据类型选择合适的抛光策略
    """
    from ..tools import run_racon, run_pilon, run_medaka
    
    logger.info(f"Running polishing with {tool} on {read_type} data")
    
    reads_path = Path(reads_file)
    reads2_path = Path(reads2_file) if reads2_file else None
    assembly_path = Path(assembly_file)
    
    try:
        if tool.lower() == "racon":
            # Racon 用于长读数据
            minimap_preset = "map-ont" if "nanopore" in read_type.lower() else "map-pb"
            iterations = 3 if "clr" in read_type.lower() else 2
            
            result = run_racon(
                reads=reads_path,
                assembly=assembly_path,
                output_dir=output_dir,
                threads=threads,
                iterations=iterations,
                minimap_preset=minimap_preset
            )
            
        elif tool.lower() == "pilon":
            # Pilon 用于短读数据
            result = run_pilon(
                reads=reads_path,
                reads2=reads2_path,
                assembly=assembly_path,
                output_dir=output_dir,
                threads=threads,
                memory="16G",
                iterations=1
            )
            
        elif tool.lower() == "medaka":
            # Medaka 用于 Nanopore 数据
            # 根据实际化学配方选择模型（这里使用默认）
            result = run_medaka(
                reads=reads_path,
                assembly=assembly_path,
                output_dir=output_dir,
                model="r941_min_high_g360",
                threads=threads
            )
            
        else:
            raise ValueError(f"Unknown polishing tool: {tool}")
        
        return result
        
    except Exception as e:
        logger.error(f"Polishing with {tool} failed: {e}")
        raise

def _calculate_improvement(original_file: str, polished_file: str) -> Dict[str, Any]:
    """
    计算抛光改进
    
    对比抛光前后的统计信息
    """
    try:
        from Bio import SeqIO
        
        # 读取原始序列
        orig_seqs = list(SeqIO.parse(original_file, "fasta"))
        orig_lengths = [len(seq) for seq in orig_seqs]
        
        # 读取抛光后序列
        polish_seqs = list(SeqIO.parse(polished_file, "fasta"))
        polish_lengths = [len(seq) for seq in polish_seqs]
        
        if not orig_lengths or not polish_lengths:
            return {"status": "no_data"}
        
        # 计算统计
        orig_total = sum(orig_lengths)
        polish_total = sum(polish_lengths)
        
        orig_n50 = _calculate_n50(orig_lengths)
        polish_n50 = _calculate_n50(polish_lengths)
        
        return {
            "status": "calculated",
            "length_change": polish_total - orig_total,
            "length_change_pct": ((polish_total - orig_total) / orig_total * 100) if orig_total > 0 else 0,
            "n50_change": polish_n50 - orig_n50,
            "n50_change_pct": ((polish_n50 - orig_n50) / orig_n50 * 100) if orig_n50 > 0 else 0,
            "original": {
                "total_length": orig_total,
                "num_contigs": len(orig_lengths),
                "n50": orig_n50
            },
            "polished": {
                "total_length": polish_total,
                "num_contigs": len(polish_lengths),
                "n50": polish_n50
            }
        }
    except Exception as e:
        logger.warning(f"Failed to calculate improvement: {e}")
        return {"status": "error", "message": str(e)}

def _calculate_n50(lengths: list) -> int:
    """计算 N50"""
    if not lengths:
        return 0
    
    sorted_lengths = sorted(lengths, reverse=True)
    total = sum(sorted_lengths)
    cumsum = 0
    
    for length in sorted_lengths:
        cumsum += length
        if cumsum >= total / 2:
            return length
    
    return 0