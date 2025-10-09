import os
from click.testing import CliRunner
from mito_forge.cli.commands.qc import qc

def test_qc_cli_expert_success(tmp_path, monkeypatch):
    # 环境变量：启用模拟成功场景与中文输出
    monkeypatch.setenv("MITO_SIM", "qc=ok")
    monkeypatch.setenv("MITO_LANG", "zh")

    # 创建一个临时输入文件以满足 exists=True
    input_file = tmp_path / "sample_R1.fastq"
    input_file.write_text("")

    runner = CliRunner()
    result = runner.invoke(qc, [str(input_file), "--detail-level", "expert"])

    # 断言退出码与关键输出
    assert result.exit_code == 0, f"CLI exited with {result.exit_code}, output: {result.output}"
    assert "质控分析完成" in result.output