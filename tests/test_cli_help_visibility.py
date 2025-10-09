import re
from click.testing import CliRunner
from mito_forge.cli.main import cli

def test_help_shows_core_commands_only_by_default():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    out = result.output

    # 核心命令应可见
    for name in ["pipeline", "status", "doctor", "menu", "run"]:
        assert re.search(rf"\b{name}\b", out), f"{name} should be visible by default"

    # 进阶命令默认不应可见
    for name in ["qc", "assembly", "annotate", "agents", "config", "model"]:
        assert not re.search(rf"\b{name}\b", out), f"{name} should be hidden by default"

def test_help_shows_all_commands_with_expert_flag():
    runner = CliRunner()
    result = runner.invoke(cli, ["--expert", "--help"])
    assert result.exit_code == 0
    out = result.output

    # 核心命令仍可见
    for name in ["pipeline", "status", "doctor", "menu", "run"]:
        assert re.search(rf"\b{name}\b", out), f"{name} should be visible with --expert"

    # 进阶命令在 --expert 时应可见
    for name in ["qc", "assembly", "annotate", "agents", "config", "model"]:
        assert re.search(rf"\b{name}\b", out), f"{name} should be visible with --expert"