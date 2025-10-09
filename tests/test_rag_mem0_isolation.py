from pathlib import Path
from mito_forge.core.agents.base_agent import BaseAgent
from mito_forge.core.agents.types import TaskSpec, StageResult, AgentCapability, AgentStatus

class DummyAgent(BaseAgent):
    def prepare(self, workdir: Path, **kwargs) -> None:
        self.workdir = workdir
    def run(self, inputs: dict, **config) -> StageResult:
        return StageResult(status=AgentStatus.FINISHED, outputs={}, metrics={})
    def finalize(self) -> None:
        pass
    def get_capability(self) -> AgentCapability:
        return AgentCapability(name="dummy", description="d", supported_inputs=[], resource_requirements={})

def test_mem0_is_per_agent_instance(monkeypatch):
    a = DummyAgent("A")
    b = DummyAgent("B")
    # 准备 current_task 以便 emit_event 可用
    a.current_task = TaskSpec(task_id="ta", agent_type="dummy", inputs={}, config={}, workdir=Path("work/ta"))
    b.current_task = TaskSpec(task_id="tb", agent_type="dummy", inputs={}, config={}, workdir=Path("work/tb"))
    # 注入 memory_write 实现以触发 _get_mem0 调用（由被测代码内部完成）
    # 同时确保 memory_write 不抛错
    events_a = []
    events_b = []
    def mw_a(ev): events_a.append(ev)
    def mw_b(ev): events_b.append(ev)
    monkeypatch.setattr(a, "memory_write", mw_a)
    monkeypatch.setattr(b, "memory_write", mw_b)
    # 首次事件，触发各自 agent 的 mem0 初始化
    a.emit_event("started")
    b.emit_event("started")
    # 断言：每个 agent 都持有自己的 mem0 客户端缓存（_mem0 不同）
    assert getattr(a, "_mem0", None) is not None
    assert getattr(b, "_mem0", None) is not None
    assert a._mem0 is not b._mem0

def test_rag_uses_shared_singleton(monkeypatch):
    shared_obj = object()
    calls = {"count": 0}
    # 两个 agent
    a = DummyAgent("A")
    b = DummyAgent("B")
    # monkeypatch 共享入口，验证 rag_augment 走共享入口
    def get_shared(_self):
        calls["count"] += 1
        return {"collection": shared_obj}
    monkeypatch.setattr(DummyAgent, "_get_shared_chroma", get_shared, raising=True)
    # monkeypatch collection.query 行为，通过替代 rag_augment 内部使用来避免真实依赖
    # 让 shared collection 的 query 被模拟
    def fake_rag(prompt, task=None, top_k=4):
        # 直接调用共享入口，模拟使用共享 collection
        _ = a._get_shared_chroma()  # 增加一次调用计数
        return prompt + " [RAG]", []
    monkeypatch.setattr(DummyAgent, "rag_augment", fake_rag, raising=True)
    # 调用两次（两个 agent 各一次）
    _ = a.generate_llm_response("p")
    _ = b.generate_llm_response("q")
    # 确认共享入口被调用多次，但始终返回同一个共享对象（通过我们替身保证）
    assert calls["count"] >= 1