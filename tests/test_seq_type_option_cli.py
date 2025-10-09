import re
from click.testing import CliRunner
from mito_forge.cli.main import cli

def test_pipeline_help_shows_seq_type_option_and_choices():
    runner = CliRunner()
    result = runner.invoke(cli, ["pipeline", "--help"])
    assert result.exit_code == 0
    out = result.output
    assert "--seq-type" in out
    # 可选值提示
    for choice in ["auto", "illumina", "ont", "pacbio-hifi", "pacbio-clr", "hybrid"]:
        assert choice in out

def test_pipeline_help_mentions_envvar_for_seq_type():
    runner = CliRunner()
    result = runner.invoke(cli, ["pipeline", "--help"])
    assert result.exit_code == 0
    out = result.output
    # Click 会在 help 中标注 Environment variable，或者在帮助描述中出现 env 名称
    assert "MITO_SEQ_TYPE" in out

def test_pipeline_help_accepts_explicit_seq_type_value():
    runner = CliRunner()
    # 仅做参数校验，不执行主体：有 --help
    result = runner.invoke(cli, ["pipeline", "--seq-type", "ont", "--help"])
    assert result.exit_code == 0
    out = result.output
    assert "--seq-type" in out
    assert "ont" in out