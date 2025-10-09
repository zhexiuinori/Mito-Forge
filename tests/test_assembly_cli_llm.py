import os
import sys
import subprocess


def test_assembly_cli_sim_ok(tmp_path):
    # 创建一个最小的 FASTQ 输入文件
    reads = tmp_path / "sample_R1.fastq"
    reads.write_text("@r1\nACGT\n+\n!!!!\n", encoding="utf-8")

    env = os.environ.copy()
    env["MITO_SIM"] = "assembly=ok"
    env["MITO_LANG"] = "zh"

    cmd = [sys.executable, "-m", "mito_forge", "assembly", str(reads)]
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)

    # 调试输出（失败时更好定位）
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    combined = stdout + "\n" + stderr

    assert proc.returncode == 0, f"assembly 命令退出码非0，输出：\n{combined}"
    assert "基因组组装完成" in combined, f"未找到成功提示，输出：\n{combined}"