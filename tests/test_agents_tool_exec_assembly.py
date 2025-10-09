from pathlib import Path
import pytest

from mito_forge.core.agents.assembly_agent import AssemblyAgent

class Recorder:
    def __init__(self):
        self.calls = []

    def __call__(self, exe, args, cwd, env=None, timeout=None, **kwargs):
        self.calls.append({"exe": exe, "args": list(args), "cwd": str(cwd), "timeout": timeout})
        return {
            "exit_code": 0,
            "stdout_path": str(Path(cwd) / "stdout.log"),
            "stderr_path": str(Path(cwd) / "stderr.log"),
            "elapsed_sec": 0.2
        }

def test_assembly_agent_executes_spades_when_available(monkeypatch, tmp_path):
    agent = AssemblyAgent(config={"threads": 4})
    agent.prepare(tmp_path)

    # 让 which 命中 spades.py
    import shutil
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/spades.py" if name.lower() in ("spades.py", "spades") else None)

    rec = Recorder()
    monkeypatch.setattr(agent, "run_tool", rec)

    reads = tmp_path / "reads.fastq"
    reads.write_text("@r\\nACGT\\n+\\n!!!!\\n")
    res = agent.run_assembly({"reads": str(reads), "assembler": "spades", "read_type": "illumina"})

    assert any("spades" in c["exe"].lower() for c in rec.calls)
    assert res.get("assembler") == "spades"

def test_assembly_agent_executes_flye_when_available(monkeypatch, tmp_path):
    agent = AssemblyAgent(config={"threads": 8})
    agent.prepare(tmp_path)

    import shutil
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/flye" if name.lower() == "flye" else None)

    rec = Recorder()
    monkeypatch.setattr(agent, "run_tool", rec)

    reads = tmp_path / "reads.fastq"
    reads.write_text("@r\\nACGT\\n+\\n!!!!\\n")
    res = agent.run_assembly({"reads": str(reads), "assembler": "flye", "read_type": "nanopore"})

    assert any(c["exe"].lower() == "flye" for c in rec.calls)
    assert res.get("assembler") == "flye"

def test_assembly_agent_falls_back_when_tool_missing(monkeypatch, tmp_path):
    agent = AssemblyAgent(config={})
    agent.prepare(tmp_path)

    import shutil
    monkeypatch.setattr(shutil, "which", lambda name: None)

    def fail_run_tool(*a, **k):
        return {"exit_code": 1, "stdout_path": "", "stderr_path": "", "elapsed_sec": 0.1}
    monkeypatch.setattr(agent, "run_tool", fail_run_tool)

    reads = tmp_path / "reads.fastq"
    reads.write_text("@r\\nACGT\\n+\\n!!!!\\n")
    res = agent.run_assembly({"reads": str(reads), "assembler": "spades", "read_type": "illumina"})

    # 回退模拟：包含统计字段
    assert "n50" in res and "num_contigs" in res