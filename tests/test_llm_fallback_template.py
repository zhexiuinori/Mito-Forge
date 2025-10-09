from pathlib import Path
from mito_forge.core.agents.base_agent import BaseAgent
from mito_forge.core.agents.types import StageResult, AgentCapability, AgentStatus

class DummyAgent(BaseAgent):
    def prepare(self, workdir: Path, **kwargs) -> None:
        self.workdir = workdir
    def run(self, inputs: dict, **config) -> StageResult:
        return StageResult(status=AgentStatus.FINISHED, outputs={}, metrics={})
    def finalize(self) -> None:
        pass
    def get_capability(self) -> AgentCapability:
        return AgentCapability(name="dummy", description="d", supported_inputs=[], resource_requirements={})

def test_generate_llm_response_template_when_provider_none(monkeypatch):
    a = DummyAgent("A")
    # 强制 provider 不可用
    monkeypatch.setattr(a, "get_llm_provider", lambda: None)
    resp = a.generate_llm_response("这是一个测试提示词，用于验证模板汇总行为。", system=None)
    assert "[LLM不可用]" in resp

def test_generate_llm_response_template_when_generate_error(monkeypatch):
    class FakeProvider:
        def generate(self, prompt, system=None, **kw):
            raise RuntimeError("network failed")
    a = DummyAgent("A")
    monkeypatch.setattr(a, "get_llm_provider", lambda: FakeProvider())
    resp = a.generate_llm_response("这是第二个测试提示词。", system=None)
    assert "[LLM错误]" in resp