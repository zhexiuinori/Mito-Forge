"""
LangGraph 图构建
定义状态机的节点连接和条件路由
"""
from typing import Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from .state import PipelineState, get_next_stage, is_pipeline_complete
from .nodes import supervisor_node, qc_node, assembly_node, polish_node, annotation_node, report_node

def build_pipeline_graph():
    """
    构建线粒体组装流水线的状态图
    
    流程：
    START → supervisor → qc → assembly → annotation → report → END
           ↑         ↓    ↓        ↓           ↓
           └─ retry ─┴────┴────────┴───────────┘
    """
    
    # 创建状态图
    graph = StateGraph(PipelineState)
    
    # 添加节点
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("qc", qc_node)
    graph.add_node("assembly", assembly_node)
    graph.add_node("polish", polish_node)
    graph.add_node("annotation", annotation_node)
    graph.add_node("report", report_node)
    
    # 设置入口点
    graph.set_entry_point("supervisor")
    
    # 添加边
    graph.add_edge("supervisor", "qc")
    graph.add_edge("qc", "assembly")
    # assembly -> polish 条件边（在下面定义）
    graph.add_edge("polish", "annotation")
    graph.add_edge("annotation", "report")
    graph.add_edge("report", END)
    
    # 添加条件边（路由决策）
    graph.add_conditional_edges(
        "supervisor",
        supervisor_route_decider,
        {
            "continue": "qc",
            "terminate": END
        }
    )
    
    graph.add_conditional_edges(
        "qc",
        stage_route_decider,
        {
            "continue": "assembly",
            "retry": "qc",
            "terminate": END
        }
    )
    
    graph.add_conditional_edges(
        "assembly", 
        assembly_route_decider,
        {
            "polish": "polish",
            "skip_polish": "annotation",
            "retry": "assembly",
            "fallback": "assembly",  # 使用备用工具重试
            "terminate": END
        }
    )
    
    graph.add_conditional_edges(
        "polish",
        stage_route_decider,
        {
            "continue": "annotation",
            "terminate": END
        }
    )
    
    graph.add_conditional_edges(
        "annotation",
        stage_route_decider,
        {
            "continue": "report",
            "retry": "annotation",
            "terminate": "report"  # 注释失败也可以生成报告
        }
    )
    
    # 编译图 (暂时不使用 checkpointer，避免配置复杂性)
    return graph.compile()
    # 如需启用检查点功能，使用:
    # return graph.compile(checkpointer=SqliteSaver.from_conn_string(":memory:"))
    
    # 以下为旧的临时实现（已启用LangGraph）
    # 旧的临时实现（保留作为备用）
    # return {
    #     "nodes": {
    #         "supervisor": supervisor_node,
    #         "qc": qc_node,
    #         "assembly": assembly_node,
    #         "annotation": annotation_node,
    #         "report": report_node
    #     },
    #     "edges": {
    #         "supervisor": ["qc"],
    #         "qc": ["assembly"],
    #         "assembly": ["annotation"],
    #         "annotation": ["report"],
    #         "report": ["END"]
    #     },
    #     "conditional_edges": {
    #         "supervisor": supervisor_route_decider,
    #         "qc": stage_route_decider,
    #         "assembly": stage_route_decider,
    #         "annotation": stage_route_decider
    #     }
    # }

def supervisor_route_decider(state: PipelineState) -> Literal["continue", "terminate"]:
    """主管节点路由决策"""
    if state["route"] == "terminate":
        return "terminate"
    return "continue"

def assembly_route_decider(state: PipelineState) -> Literal["polish", "skip_polish", "retry", "fallback", "terminate"]:
    """组装节点路由决策 - 决定是否需要抛光"""
    route = state["route"]
    
    if route == "terminate":
        return "terminate"
    elif route == "retry":
        return "retry"
    elif route == "fallback":
        return "fallback"
    
    # 检查是否需要抛光
    tool_chain = state.get("config", {}).get("tool_chain", {})
    polishing_tool = tool_chain.get("polishing")
    
    if polishing_tool:
        return "polish"
    else:
        return "skip_polish"

def stage_route_decider(state: PipelineState) -> Literal["continue", "retry", "fallback", "terminate"]:
    """阶段节点路由决策"""
    route = state["route"]
    
    if route == "terminate":
        return "terminate"
    elif route == "retry":
        return "retry"
    elif route == "fallback":
        return "fallback"
    else:
        return "continue"

def run_pipeline_sync(
    inputs: dict,
    config: dict,
    workdir: str,
    pipeline_id: str = None
) -> PipelineState:
    """
    同步运行流水线（使用 LangGraph）
    """
    from .state import init_pipeline_state
    
    # 初始化状态
    state = init_pipeline_state(inputs, config, workdir, pipeline_id)
    
    # 构建并编译 LangGraph
    compiled_graph = build_pipeline_graph()
    
    # 配置 LangGraph 执行 (添加必需的 thread_id)
    run_config = {
        "configurable": {
            "thread_id": pipeline_id or state.get("pipeline_id", "default")
        }
    }
    
    # 使用 LangGraph 执行流水线
    final_state = compiled_graph.invoke(state, config=run_config)
    
    return final_state

# === 检查点和持久化 ===

def save_checkpoint(state: PipelineState, checkpoint_path: str):
    """保存检查点"""
    import json
    from pathlib import Path
    
    checkpoint_file = Path(checkpoint_path)
    checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
    
    with checkpoint_file.open("w") as f:
        json.dump(state, f, indent=2, default=str)

def load_checkpoint(checkpoint_path: str) -> PipelineState:
    """加载检查点"""
    import json
    from pathlib import Path
    
    checkpoint_file = Path(checkpoint_path)
    if not checkpoint_file.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
    
    with checkpoint_file.open("r") as f:
        return json.load(f)

def resume_pipeline(checkpoint_path: str) -> PipelineState:
    """从检查点恢复流水线"""
    state = load_checkpoint(checkpoint_path)
    
    # 确定从哪个阶段恢复
    current_stage = state["current_stage"]
    print(f"Resuming pipeline from stage: {current_stage}")
    
    # 继续执行（这里需要根据当前阶段调整执行逻辑）
    graph_config = build_pipeline_graph()
    nodes = graph_config["nodes"]
    
    # 从当前阶段开始执行
    remaining_stages = []
    all_stages = ["supervisor", "qc", "assembly", "annotation", "report"]
    
    start_index = all_stages.index(current_stage) if current_stage in all_stages else 0
    remaining_stages = all_stages[start_index:]
    
    for node_name in remaining_stages:
        if state["done"] or state["route"] == "terminate":
            break
            
        print(f"Executing {node_name}...")
        node_func = nodes[node_name]
        state = node_func(state)
        
        # 保存中间检查点
        save_checkpoint(state, checkpoint_path)
    
    return state