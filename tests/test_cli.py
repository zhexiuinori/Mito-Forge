"""
CLI模块测试
"""

import pytest
from click.testing import CliRunner
from mito_forge.cli.main import main


class TestCLI:
    """CLI测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.runner = CliRunner()
    
    def test_main_help(self):
        """测试主帮助命令"""
        result = self.runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert 'Mito-Forge' in result.output
    
    def test_pipeline_help(self):
        """测试pipeline帮助命令"""
        result = self.runner.invoke(main, ['pipeline', '--help'])
        assert result.exit_code == 0
        assert 'pipeline' in result.output.lower()
    
    def test_config_show(self):
        """测试配置显示"""
        result = self.runner.invoke(main, ['config', 'show'])
        assert result.exit_code == 0
    
    def test_doctor_check(self):
        """测试系统检查"""
        result = self.runner.invoke(main, ['doctor'])
        assert result.exit_code == 0