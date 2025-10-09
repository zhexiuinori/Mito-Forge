import os
from pathlib import Path
import json
import types

import pytest

from mito_forge.core.agents.qc_agent import QCAgent

class Recorder:
    def __init__(self):
        self.calls = []

    def __call__(self, exe, args, cwd, env=None, timeout=None, **kwargs):
        self.calls.append({"exe": exe, "args": list(args), "cwd": str(cwd), "timeout": timeout})
        # 模拟执行成功
        return {
            "exit_code": 0,
            "stdout_path": str(Path(cwd) / "stdout.log"),
            "stderr_path": str(Path(cwd) / "stderr.log"),
            "elapsed_sec": 0.1
        }

def test_qc_agent_executes_fastqc_when_available(monkeypatch, tmp_path):
    agent = QCAgent(config={"detail_level": "quick"})
    agent.prepare(tmp_path)

    # 强制选择 fastqc 路径：让 which 返回非空
    import shutil
    monkeypatch.setattr(shutil, "which", lambda name: "C:/bin/fastqc" if name.lower() == "fastqc" else None)

    # 记录 run_tool 调用
    rec = Recorder()
    monkeypatch.setattr(agent, "run_tool", rec)

    inputs = {"reads": str(tmp_path / "reads.fastq"), "read_type": "illumina"}
    (tmp_path / "reads.fastq").write_text("@r\\nACGT\\n+\\n!!!!\\n")

    res = agent.run_qc_analysis(inputs)

    # 断言调用了 fastqc
    assert any(c["exe"].lower() == "fastqc" for c in rec.calls)
    # 仍需返回结构化结果
    assert "filename" in res and res["filename"].endswith("reads.fastq")

def test_qc_agent_falls_back_when_tool_missing(monkeypatch, tmp_path):
    agent = QCAgent(config={})
    agent.prepare(tmp_path)

    # which 缺失
    import shutil
    monkeypatch.setattr(shutil, "which", lambda name: None)

    # 若 run_tool 被调用也强制失败
    def fail_run_tool(*a, **k):
        return {"exit_code": 1, "stdout_path": "", "stderr_path": "", "elapsed_sec": 0.1}
    monkeypatch.setattr(agent, "run_tool", fail_run_tool)

    inputs = {"reads": str(tmp_path / "reads.fastq")}
    (tmp_path / "reads.fastq").write_text("@r\\nACGT\\n+\\n!!!!\\n")

    res = agent.run_qc_analysis(inputs)
    # 回退模拟：包含我们现有字段
    assert "avg_quality" in res and isinstance(res["avg_quality"], (int, float))

def test_qc_agent_dry_run_skips_execution(monkeypatch, tmp_path):
    agent = QCAgent(config={"dry_run": True})
    agent.prepare(tmp_path)

    # 如果被调用则抛异常，确保未触发
    def bomb(*a, **k):
        raise AssertionError("run_tool should not be called in dry_run")
    monkeypatch.setattr(agent, "run_tool", bomb)

    inputs = {"reads": str(tmp_path / "reads.fastq")}
    (tmp_path / "reads.fastq").write_text("@r\\nACGT\\n+\\n!!!!\\n")

    res = agent.run_qc_analysis(inputs)
    assert "total_reads" in res