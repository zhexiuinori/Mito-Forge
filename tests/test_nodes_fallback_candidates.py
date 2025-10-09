import time
from pathlib import Path
import types
import mito_forge.graph.nodes as nodes

def make_state(tmp_path, plan):
    workdir = tmp_path / "work"
    workdir.mkdir(parents=True, exist_ok=True)
    reads = tmp_path / "reads.fastq"
    reads.write_text("@r1\nACGT\n+\n!!!!\n")
    state = {
        "pipeline_id": "test-fallback",
        "inputs": {"reads": str(reads), "kingdom": "animal"},
        "stage_info": {"supervisor": {}, "assembly": {}, "qc": {}},
        "stage_outputs": {},
        "completed_stages": [],
        "failed_stages": [],
        "global_metrics": {},
        "config": {"kingdom": "animal", "tool_plan": plan},
        "workdir": str(workdir),
        "current_stage": "supervisor",
        "route": "continue",
        "retries": {"assembly": 2},  # 直接触发回退路径
        "done": False,
        "errors": [],
        "start_time": time.time(),
    }
    return state

def test_assembly_fallback_uses_plan_candidates(monkeypatch, tmp_path):
    plan = {
        "qc": ["fastqc"],
        "assembler": {"name": "flye", "params": {}},
        "polishers": ["racon"],
        "candidates": {"assembler": ["flye", "spades", "unicycler"]},
    }
    state = make_state(tmp_path, plan)
    # 先跑 supervisor 让 tool_chain 生效
    state = nodes.supervisor_node(state)
    # 把 _run_assembly 打补丁为抛异常，模拟失败
    def boom(*args, **kwargs):
        raise RuntimeError("boom")
    monkeypatch.setattr(nodes, "_run_assembly", boom)
    # 进入组装节点，应选择使用候选回退
    out = nodes.assembly_node(state)
    # 当 retries>=2 时 nodes 中进入回退分支，使用候选的下一个工具
    assert out["route"] in ("fallback", "terminate")
    # 如果有回退工具，config.tool_chain.assembly 应更新为候选列表中的后续工具之一
    fallback_tool = out["config"]["tool_chain"]["assembly"]
    assert fallback_tool in ("spades", "unicycler")