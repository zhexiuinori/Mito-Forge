import types
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
        return AgentCapability(
            name="dummy",
            description="dummy",
            supported_inputs=[],
            resource_requirements={}
        )

def test_rag_called_in_generate_llm_response(monkeypatch):
    called = {"rag": False}
    agent = DummyAgent("dummy", config={"enable_rag": True})
    def wrapper(prompt, task=None, top_k=4):
        called["rag"] = True
        return (prompt + " [RAG]", [])
    monkeypatch.setattr(agent, "rag_augment", wrapper)
    _ = agent.generate_llm_response("hello world", system=None)
    assert called["rag"] is True

def test_memory_write_called_on_emit_events(monkeypatch):
    events = []
    agent = DummyAgent("dummy", config={"enable_memory": True})
    agent.current_task = TaskSpec(task_id="t1", agent_type="dummy", inputs={}, config={}, workdir=Path("work/t1"))
    def mem_write(event):
        events.append(event)
    monkeypatch.setattr(agent, "memory_write", mem_write)
    agent.emit_event("started", info="begin")
    agent.emit_event("finished", info="done")
    agent.emit_event("error", error="oops")
    assert len(events) == 3
    assert events[0]["event_type"] == "started"
    assert events[1]["event_type"] == "finished"
    assert events[2]["event_type"] == "error"

def test_rag_enabled_by_default_when_no_config(monkeypatch):
    called = {"rag": False}
    agent = DummyAgent("dummy")  # no config provided
    def wrapper(prompt, task=None, top_k=4):
        called["rag"] = True
        return (prompt + " [RAG]", [])
    monkeypatch.setattr(agent, "rag_augment", wrapper)
    _ = agent.generate_llm_response("test", system=None)
    assert called["rag"] is True

def test_memory_enabled_by_default_when_no_config(monkeypatch):
    events = []
    agent = DummyAgent("dummy")  # no config provided
    agent.current_task = TaskSpec(task_id="t2", agent_type="dummy", inputs={}, config={}, workdir=Path("work/t2"))
    def mem_write(event):
        events.append(event)
    monkeypatch.setattr(agent, "memory_write", mem_write)
    agent.emit_event("started")
    assert len(events) == 1
    assert events[0]["event_type"] == "started"