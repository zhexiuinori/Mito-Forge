import time
from pathlib import Path
from mito_forge.graph.nodes import supervisor_node, qc_node, assembly_node

def make_base_state(tmp_path, plan):
    workdir = tmp_path / "work"
    workdir.mkdir(parents=True, exist_ok=True)
    reads = tmp_path / "reads.fastq"
    reads.write_text("@r1\nACGT\n+\n!!!!\n")
    state = {
        "pipeline_id": "test-apply-params",
        "inputs": {"reads": str(reads), "kingdom": "animal"},
        "stage_info": {"supervisor": {}, "qc": {}, "assembly": {}},
        "stage_outputs": {},
        "completed_stages": [],
        "failed_stages": [],
        "global_metrics": {},
        "config": {
            "kingdom": "animal",
            "tool_plan": plan,
        },
        "workdir": str(workdir),
        "current_stage": "supervisor",
        "route": "continue",
        "retries": {},
        "done": False,
        "errors": [],
        "start_time": time.time(),
    }
    return state

def test_qc_and_assembly_use_params_from_tool_plan(tmp_path):
    plan = {
        "qc": ["fastqc"],
        "assembler": {"name": "flye", "params": {"--genome-size": "16k", "--iterations": 2}},
        "polishers": ["racon", "medaka"],
        "hints": {"kingdom": "animal", "input_types": ["FASTQ"]},
    }
    state = make_base_state(tmp_path, plan)
    # supervisor 消费 plan 并下发 tool_chain/parameters
    state = supervisor_node(state)
    assert state["route"] in ("continue", "END")
    # 运行 QC 节点，参数应被写入 used_params.json
    state = qc_node(state)
    qc_dir = Path(state["workdir"]) / "01_qc"
    qc_used = qc_dir / "qc_used_params.json"
    assert qc_used.exists(), "应写出 QC 使用的参数文件以证明参数已生效"
    # 运行组装节点，参数应被写入 used_params.json
    state = assembly_node(state)
    asm_dir = Path(state["workdir"]) / "02_assembly"
    asm_used = asm_dir / "assembly_used_params.json"
    assert asm_used.exists(), "应写出 Assembly 使用的参数文件以证明参数已生效"
    # 校验参数中包含 genome-size 与 iterations
    import json
    asm_params = json.loads(asm_used.read_text(encoding="utf-8"))
    assert asm_params.get("--genome-size") == "16k"
    assert asm_params.get("--iterations") == 2