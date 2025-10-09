from click.testing import CliRunner
import types
import builtins

# 假定主入口命令为 mito_forge.cli.main:cli
from mito_forge.cli.main import cli


def test_doctor_reports_missing_tools(monkeypatch):
    # 模拟 which：所有工具都找不到
    import shutil

    def fake_which(name):
        return None

    monkeypatch.setattr(shutil, "which", fake_which)

    runner = CliRunner()
    result = runner.invoke(cli, ["doctor", "--tools", "spades,flye,pilon,racon,medaka,minimap2"])
    assert result.exit_code == 0
    out = result.output.lower()
    assert "missing" in out or "缺失" in out
    # 至少缺少两个典型工具
    for t in ["spades", "flye"]:
        assert t in out


def test_doctor_reports_present_tools(monkeypatch, tmp_path):
    # 模拟 which：仅 spades 和 flye 存在
    import shutil

    def fake_which(name):
        return str(tmp_path / f"{name}.exe") if name in {"spades", "flye"} else None

    monkeypatch.setattr(shutil, "which", fake_which)

    from mito_forge.cli.main import cli  # 重新导入以确保 monkeypatch 生效
    runner = CliRunner()
    result = runner.invoke(cli, ["doctor", "--tools", "spades,flye,pilon,racon,medaka,minimap2"])
    assert result.exit_code == 0
    out = result.output.lower()
    # 应报告 present 和 missing
    assert "present" in out or "已安装" in out
    assert "missing" in out or "缺失" in out
    assert "spades" in out and "flye" in out
    # 仍应包含缺失的其它工具名
    assert "pilon" in out and "racon" in out and "medaka" in out and "minimap2" in out