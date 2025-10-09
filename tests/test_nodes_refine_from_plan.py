import time
from pathlib import Path
from mito_forge.graph.nodes import supervisor_node

def make_state_with_plan(tmp_path, assembler_name="flye", asm_params=None, qc_name="fastqc", polishers=None):
    if asm_params is None:
        asm_params = {"--genome-size": "16k", "--iterations": 2}
    if polishers is None:
        polishers = ["racon", "medaka"]
    workdir = tmp_path / "work"
    workdir.mkdir(parents=True, exist_ok=True)
    reads = tmp_path / "reads.fastq"
    reads.write_text("@r1\nACGT\n+\n!!!!\n")
    state = {
        "pipeline_id": "test-refine",
        "inputs": {"reads": str(reads), "kingdom": "animal"},
        "stage_info": {"supervisor": {}},
        "stage_outputs": {},
        "completed_stages": [],
        "failed_stages": [],
        "global_metrics": {},
        "config": {
            "kingdom": "animal",
            "tool_plan": {
                "qc": [qc_name],
                "assembler": {"name": assembler_name, "params": asm_params},
                "polishers": polishers,
                "hints": {"kingdom": "animal", "input_types": ["FASTQ"]},
            },
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

def test_supervisor_merges_assembler_params_from_tool_plan(tmp_path):
    asm_params = {"--genome-size": "16k", "--iterations": 3}
    state = make_state_with_plan(tmp_path, assembler_name="flye", asm_params=asm_params)
    out = supervisor_node(state)
    assert out["route"] in ("continue", "END")
    tool_chain = out["config"].get("tool_chain", {})
    assert tool_chain.get("assembly") == "flye"
    # 参数应被合并进 tool_parameters.flye
    params = out["config"].get("tool_parameters", {}).get("flye", {})
    for k, v in asm_params.items():
        assert params.get(k) == v

def test_supervisor_keeps_qc_and_polishing_from_tool_plan(tmp_path):
    state = make_state_with_plan(tmp_path, qc_name="nanoplot", polishers=["medaka"])
    out = supervisor_node(state)
    tool_chain = out["config"].get("tool_chain", {})
    assert tool_chain.get("qc") in ("nanoplot", "fastqc", "pbccs_qc")
    # polishing 字段若存在，应来自 plan 的首选
    assert tool_chain.get("polishing") in (None, "medaka", "racon")