import os
import sys
import subprocess

def test_qc_cli_llm_ok(tmp_path):
    # 准备最小 FASTQ 输入
    p = tmp_path / "reads.fastq"
    p.write_text("@seq\nACGT\n+\nIIII\n", encoding="utf-8")

    env = os.environ.copy()
    # 使用真实 LLM，取消模拟
    env.pop("MITO_SIM", None)
    env["MITO_LANG"] = "zh"

    cmd = [sys.executable, "-m", "mito_forge", "qc", str(p)]
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)

    # 正常完成
    assert proc.returncode == 0
    # 包含完成提示（中文或英文）
    assert ("质控分析完成" in proc.stdout) or ("QC analysis completed" in proc.stdout)