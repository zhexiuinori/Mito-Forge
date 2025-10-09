import json
from click.testing import CliRunner
import types

def _fake_state():
    # 构造最小可用的流水线状态，避免后续摘要输出报错
    return {
        "pipeline_id": "test-pipe",
        "done": True,
        "current_stage": "done",
        "completed_stages": [],
        "stage_outputs": {},
        "errors": [],
        "warnings": [],
        "start_time": 0.0,
        "end_time": 0.0,
    }

def test_pipeline_injects_tool_plan_with_explicit_seq_type_ont(monkeypatch):
    captured = {}

    def fake_run_pipeline_sync(inputs, config, workdir, pipeline_id):
        captured["inputs"] = inputs
        captured["config"] = config
        captured["workdir"] = workdir
        captured["pipeline_id"] = pipeline_id
        return _fake_state()

    # 拦截 pipeline 模块命名空间中的符号（pipeline.py 顶层已 from ...graph.build import run_pipeline_sync）
    import mito_forge.cli.commands.pipeline as pl_mod
    monkeypatch.setattr(pl_mod, "run_pipeline_sync", fake_run_pipeline_sync, raising=True)

    from mito_forge.cli.main import cli
    runner = CliRunner()
    # 使用仓库根已有的 test.fastq
    result = runner.invoke(cli, ["pipeline", "--reads", "test.fastq", "--seq-type", "ont"])
    assert result.exit_code == 0, result.output

    plan = captured["config"].get("tool_plan")
    assert plan is not None
    assert plan["assembler"]["name"] == "flye"

def test_pipeline_injects_tool_plan_with_auto_detection(monkeypatch):
    captured = {}

    def fake_run_pipeline_sync(inputs, config, workdir, pipeline_id):
        captured["inputs"] = inputs
        captured["config"] = config
        captured["workdir"] = workdir
        captured["pipeline_id"] = pipeline_id
        return _fake_state()

    # 拦截 pipeline 模块命名空间中的符号（pipeline.py 顶层已 from ...graph.build import run_pipeline_sync）
    import mito_forge.cli.commands.pipeline as pl_mod
    monkeypatch.setattr(pl_mod, "run_pipeline_sync", fake_run_pipeline_sync, raising=True)

    from mito_forge.cli.main import cli
    runner = CliRunner()
    # 自动探测：单个 reads 为 R1.fastq 的模式应判断为 illumina
    result = runner.invoke(cli, ["pipeline", "--reads", "test.fastq", "--seq-type", "auto"])
    assert result.exit_code == 0, result.output

    plan = captured["config"].get("tool_plan")
    assert plan is not None
    # illumina 映射 spades
    assert plan["assembler"]["name"] in ("spades",)