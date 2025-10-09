import os
import sys
import json
import subprocess
from pathlib import Path


def run_cli(args, env=None, cwd=None):
    env_full = os.environ.copy()
    if env:
        env_full.update(env)
    cmd = [sys.executable, "-m", "mito_forge", "pipeline"] + args
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=cwd, env=env_full)
    return proc.returncode, proc.stdout


def test_pipeline_summary_snapshot_zh(snapshot, tmp_path):
    reads = tmp_path / "reads.fastq"
    reads.write_text("@r1\nACGT\n+\nIIII\n")
    outdir = tmp_path / "results"

    code, out = run_cli(
        ["--reads", str(reads), "--output", str(outdir), "--threads", "1", "--kingdom", "animal", "--lang", "zh"],
        env={"MITO_LANG": "zh"}
    )
    assert code == 0
    snapshot.assert_match(out, "pipeline_summary_zh.txt")


def test_pipeline_summary_json(tmp_path):
    reads = tmp_path / "reads.fastq"
    reads.write_text("@r1\nACGT\n+\nIIII\n")
    outdir = tmp_path / "results"

    code, out = run_cli(
        ["--reads", str(reads), "--output", str(outdir), "--threads", "1", "--kingdom", "animal", "--lang", "zh"],
        env={"MITO_LANG": "zh"}
    )
    assert code == 0

    # 验证结构化报告 summary.json 存在并包含三阶段聚合
    summary_path = Path(outdir) / "work" / "report" / "summary.json"
    assert summary_path.exists(), f"summary.json not found at {summary_path}"

    data = json.loads(summary_path.read_text(encoding="utf-8"))
    # 顶层包含核心字段
    assert "state" in data or ("inputs" in data and "stage_outputs" in data), "summary JSON missing core keys"

    # 兼容 nodes._generate_report 写入的内容：可能直接序列化 state
    state_obj = data.get("state", data)
    assert "stage_outputs" in state_obj, "stage_outputs missing in summary JSON"
    stage_outputs = state_obj["stage_outputs"]

    # 三阶段聚合检查（存在键即可）
    assert "qc" in stage_outputs, "qc outputs missing"
    assert "assembly" in stage_outputs, "assembly outputs missing"
    assert "annotation" in stage_outputs, "annotation outputs missing"