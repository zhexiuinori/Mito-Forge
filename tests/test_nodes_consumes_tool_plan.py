import time
from pathlib import Path

from mito_forge.graph.nodes import supervisor_node

def make_state_with_plan(tmp_path, assembler_name="flye", qc_name="fastqc", polishers=None):
    if polishers is None:
        polishers = ["racon", "medaka"]
    workdir = tmp_path / "work"
    workdir.mkdir(parents=True, exist_ok=True)
    # 最小可运行状态
    state = {
        "pipeline_id": "test-pipeline",
        "inputs": {"reads": str(tmp_path / "reads.fastq"), "kingdom": "animal"},
        "stage_info": {"supervisor": {}},
        "stage_outputs": {},
        "completed_stages": [],
        "failed_stages": [],
        "global_metrics": {},
        "config": {
            "kingdom": "animal",
            # 提供 tool_plan，期望优先被消费
            "tool_plan": {
                "qc": [qc_name],
                "assembler": {"name": assembler_name, "params": {}},
                "polishers": polishers,
                # 兼容扩展字段
                "candidates": {},
                "extras": {},
                "hints": {"kingdom": "animal", "input_types": ["FASTQ"]},
            },
        },
        "workdir": str(workdir),
        "current_stage": "supervisor",
        "completed_stages": [],
        "stage_outputs": {},
        "route": "continue",
        "retries": {},
        "done": False,
        "errors": [],
        "start_time": time.time(),
    }
    # 写一个空的 reads 文件供文件信息统计
    Path(state["inputs"]["reads"]).write_text("@r1\nACGT\n+\n!!!!\n")
    return state

def test_supervisor_prefers_tool_plan_over_internal_strategy(tmp_path):
    state = make_state_with_plan(tmp_path, assembler_name="flye")
    out = supervisor_node(state)
    # supervisor 应填充 config.tool_chain，并使用 plan 中的 assembler
    tool_chain = out["config"].get("tool_chain", {})
    assert tool_chain, "tool_chain 应由 supervisor 写入"
    assert tool_chain.get("assembly") == "flye", "应优先采用 tool_plan 的 assembler"
    # QC 若映射到单工具名，也应保持
    assert tool_chain.get("qc") in ("fastqc", "nanoplot", "pbccs_qc"), "应从 plan.qc 或内部策略选择的QC之一"
    # polishing 可选存在或为空，但如果 plan 有，则应反映到配置的 parameters/fallbacks 中
    # 这里仅检查 supervisor 成功运行并未忽略 plan
    assert out["route"] in ("continue", "END"), "supervisor 应正常结束路由"