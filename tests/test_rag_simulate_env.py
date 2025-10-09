import os
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

def test_rag_augment_simulated(monkeypatch):
    # 开启模拟
    monkeypatch.setenv("MITO_RAG_SIMULATE", "1")
    a = DummyAgent("A")
    prompt = "请给出组装最佳实践"
    aug, citations = a.rag_augment(prompt, top_k=4)
    assert aug != prompt, "模拟模式下应返回增强文本"
    assert isinstance(citations, list) and len(citations) >= 1
    assert any("模拟知识库条目" in c.get("title","") for c in citations)

def test_rag_augment_normal_no_sim(monkeypatch):
    # 关闭模拟，且移除 chromadb 相关模块，期望回退到原始提示
    for m in ["chromadb", "chromadb.utils.embedding_functions"]:
        monkeypatch.delenv(m, raising=False)
    monkeypatch.delenv("MITO_RAG_SIMULATE", raising=False)
    a = DummyAgent("A")
    prompt = "这是一个普通提示"
    aug, citations = a.rag_augment(prompt, top_k=4)
    assert aug == prompt
    assert citations == []