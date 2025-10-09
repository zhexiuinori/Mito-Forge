import os
import sys
import subprocess


def test_annotation_cli_sim_ok(tmp_path):
    # 创建一个最小的 FASTA 输入文件
    fasta = tmp_path / "contigs.fasta"
    fasta.write_text(">contig1\nACGTACGTACGT\n", encoding="utf-8")

    env = os.environ.copy()
    env["MITO_SIM"] = "annotate=ok"
    env["MITO_LANG"] = "zh"

    cmd = [sys.executable, "-m", "mito_forge", "annotate", str(fasta)]
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    combined = stdout + "\n" + stderr

    assert proc.returncode == 0, f"annotate 命令退出码非0，输出：\n{combined}"
    assert "注释完成" in combined or "Annotation completed" in combined, f"未找到成功提示，输出：\n{combined}"