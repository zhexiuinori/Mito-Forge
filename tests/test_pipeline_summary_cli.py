import os
import sys
import subprocess
from pathlib import Path


def run_cli(args, env=None, cwd=None):
    env_full = os.environ.copy()
    if env:
        env_full.update(env)
    cmd = [sys.executable, "-m", "mito_forge", "pipeline"] + args
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=cwd, env=env_full)
    return proc.returncode, proc.stdout


def test_pipeline_summary_zh(tmp_path):
    # 准备最小输入文件
    reads = tmp_path / "reads.fastq"
    reads.write_text("@r1\nACGT\n+\nIIII\n")
    outdir = tmp_path / "results"

    code, out = run_cli(
        ["--reads", str(reads), "--output", str(outdir), "--threads", "1", "--kingdom", "animal", "--lang", "zh"],
        env={"MITO_LANG": "zh"}
    )

    assert code == 0
    # 摘要标题与关键字段
    assert "摘要" in out or "summary" in out  # _t('summary_title') 中文或英文
    assert "pipeline_id" in out
    # 主输出汇总
    assert "qc_report" in out
    assert "mito_seq" in out or "assembly_stats" in out
    assert "gff" in out or "table" in out
    assert "final_report" in out