import types
from pathlib import Path
import sys

import pytest

from mito_forge.core.agents.base_agent import BaseAgent
from mito_forge.core.agents.types import AgentCapability, StageResult

class DummyAgent(BaseAgent):
    def prepare(self, workdir: Path, **kwargs) -> None:
        self.workdir = workdir
        self.logs_dir = workdir

    def run(self, inputs, **config) -> StageResult:
        return StageResult(status=None)

    def finalize(self) -> None:
        pass

    def get_capability(self) -> AgentCapability:
        # 返回最小占位
        return AgentCapability(
            name="dummy",
            description="",
            supported_inputs=[],
            resource_requirements={"cpu_cores":1,"memory_gb":1,"disk_gb":1,"estimated_time_sec":1},
        )

class _Completed:
    def __init__(self, returncode=0):
        self.returncode = returncode

def test_run_tool_fallback_to_tools_bin(monkeypatch, tmp_path: Path):
    # 1) PATH 中找不到
    import shutil, subprocess
    monkeypatch.setattr(shutil, "which", lambda *a, **k: None)

    # 2) 准备一个假的工具路径（不需要真实存在，因我们会mock subprocess.run）
    fake_tool = tmp_path / "bin" / "pmat2"
    fake_tool.parent.mkdir(parents=True, exist_ok=True)

    # 3) 注入假的 ToolsManager 到动态导入的模块命名空间
    #    run_tool 内部 "from ...utils.tools_manager import ToolsManager"
    #    我们在 sys.modules 中放置 mito_forge.utils.tools_manager 并提供 Fake ToolsManager
    mod_name = "mito_forge.utils.tools_manager"
    fake_mod = types.SimpleNamespace()

    class FakeTM:
        def __init__(self, project_root=None):
            self.project_root = project_root
        def where(self, name, version=None):
            # 返回伪造的工具路径
            return str(fake_tool)

    fake_mod.ToolsManager = FakeTM
    sys.modules[mod_name] = fake_mod

    # 4) 拦截 subprocess.run，验证调用使用的是 fake_tool
    calls = {}
    def _fake_run(cmd, cwd=None, env=None, stdout=None, stderr=None, timeout=None, shell=False, check=False):
        calls["cmd"] = cmd
        calls["cwd"] = cwd
        return _Completed(0)

    monkeypatch.setattr(subprocess, "run", _fake_run)

    # 5) 执行
    agent = DummyAgent("dummy")
    agent.prepare(tmp_path)
    result = agent.run_tool("pmat2", ["--version"], cwd=tmp_path)

    # 6) 断言：使用了 fallback 路径
    assert isinstance(calls.get("cmd"), list)
    assert Path(calls["cmd"][0]) == fake_tool
    assert calls["cmd"][1:] == ["--version"]
    assert Path(calls["cwd"]) == tmp_path

    # 7) 断言：返回码与日志文件
    assert result["exit_code"] == 0
    assert Path(result["stdout_path"]).exists()
    assert Path(result["stderr_path"]).exists()