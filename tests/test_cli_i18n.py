import os
import subprocess
import sys
import textwrap

def run_cli(args, env=None):
    cmd = [sys.executable, "-m", "mito_forge.cli.main"] + args
    base_env = os.environ.copy()
    # 屏蔽 RuntimeWarning，避免污染快照
    base_env["PYTHONWARNINGS"] = "ignore::RuntimeWarning"
    base_env["PYTHONIOENCODING"] = "UTF-8"
    if env:
        base_env.update(env)
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=base_env,
    )
    # 规范换行，去除尾随空白
    out = proc.stdout.replace("\r\n", "\n").rstrip()
    return proc.returncode, out

# CONFIG --help
def test_config_help_zh(snapshot):
    code, out = run_cli(["config", "--help"], env={"MITO_LANG": "zh"})
    assert code == 0
    assert out == snapshot

def test_config_help_en(snapshot):
    code, out = run_cli(["config", "--help"], env={"MITO_LANG": "en"})
    assert code == 0
    assert out == snapshot

# MODEL --help
def test_model_help_zh(snapshot):
    code, out = run_cli(["model", "--help"], env={"MITO_LANG": "zh"})
    assert code == 0
    assert out == snapshot

def test_model_help_en(snapshot):
    code, out = run_cli(["model", "--help"], env={"MITO_LANG": "en"})
    assert code == 0
    assert out == snapshot

# PIPELINE --help
def test_pipeline_help_zh(snapshot):
    code, out = run_cli(["pipeline", "--help"], env={"MITO_LANG": "zh"})
    assert code == 0
    assert out == snapshot

def test_pipeline_help_en(snapshot):
    code, out = run_cli(["pipeline", "--help"], env={"MITO_LANG": "en"})
    assert code == 0
    assert out == snapshot

# QC --help
def test_qc_help_zh(snapshot):
    code, out = run_cli(["qc", "--help"], env={"MITO_LANG": "zh"})
    assert code == 0
    assert out == snapshot

def test_qc_help_en(snapshot):
    code, out = run_cli(["qc", "--help"], env={"MITO_LANG": "en"})
    assert code == 0
    assert out == snapshot

# ASSEMBLY --help
def test_assembly_help_zh(snapshot):
    code, out = run_cli(["assembly", "--help"], env={"MITO_LANG": "zh"})
    assert code == 0
    assert out == snapshot

def test_assembly_help_en(snapshot):
    code, out = run_cli(["assembly", "--help"], env={"MITO_LANG": "en"})
    assert code == 0
    assert out == snapshot

# ANNOTATE --help
def test_annotate_help_zh(snapshot):
    code, out = run_cli(["annotate", "--help"], env={"MITO_LANG": "zh"})
    assert code == 0
    assert out == snapshot

def test_annotate_help_en(snapshot):
    code, out = run_cli(["annotate", "--help"], env={"MITO_LANG": "en"})
    assert code == 0
    assert out == snapshot

# --- Simulation smoke tests (Windows safe) ---
def test_qc_sim_ok_zh(snapshot):
    code, out = run_cli(
        ["qc", "test.fastq", "--report-only"],
        env={"MITO_LANG": "zh", "MITO_SIM": "qc=ok"},
    )
    assert code == 0
    assert out == snapshot

def test_assembly_sim_assembler_not_found_en(snapshot):
    code, out = run_cli(
        ["assembly", "test.fastq"],
        env={"MITO_LANG": "en", "MITO_SIM": "assembly=assembler_not_found"},
    )
    assert code != 0
    assert out == snapshot

def test_annotate_sim_db_missing_zh(snapshot):
    code, out = run_cli(
        ["annotate", "test.fastq"],
        env={"MITO_LANG": "zh", "MITO_SIM": "annotate=db_missing"},
    )
    assert code != 0
    assert out == snapshot