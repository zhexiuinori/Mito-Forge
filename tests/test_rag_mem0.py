import sys
import types
import pytest
from pathlib import Path

# Create a minimal DummyAgent to exercise BaseAgent hooks
from mito_forge.core.agents.base_agent import BaseAgent
from mito_forge.core.agents.types import StageResult, AgentCapability

class DummyAgent(BaseAgent):
    def __init__(self, config=None):
        super().__init__("dummy", config or {})

    def prepare(self, workdir: Path, **kwargs) -> None:
        self.workdir = Path(workdir)
        self.workdir.mkdir(parents=True, exist_ok=True)

    def run(self, inputs, **config) -> StageResult:
        return StageResult(status=None, outputs={"ok": True})

    def finalize(self) -> None:
        pass

    def get_capability(self) -> AgentCapability:
        return AgentCapability(
            name="dummy",
            supported_inputs=[],
            resource_requirements={"cpu_cores": 1, "memory_gb": 1, "disk_gb": 1, "estimated_time_sec": 1},
        )

# ---------- Fallback tests (no dependencies available) ----------

def test_rag_fallback_when_chromadb_missing(monkeypatch):
    # Ensure import fails or module absent
    if "chromadb" in sys.modules:
        del sys.modules["chromadb"]

    dummy = DummyAgent()
    prompt = "Test prompt for RAG"
    aug, citations = dummy.rag_augment(prompt, task=None, top_k=3)

    assert aug == prompt, "When chromadb is unavailable, prompt should not be augmented"
    assert citations == [], "Citations should be empty in fallback"


def test_mem0_fallback_when_sdk_missing(monkeypatch, capsys):
    # Ensure mem0 is absent
    if "mem0" in sys.modules:
        del sys.modules["mem0"]

    dummy = DummyAgent()
    items = dummy.memory_query(tags=["qc", "fileX"], top_k=2)
    assert items == [], "Fallback memory_query should return empty list without mem0"

    # memory_write should not raise
    dummy.memory_write({"agent": "qc", "summary": "ok"})
    # no exception -> pass

# ---------- Available path tests using lightweight stubs ----------

def _install_chromadb_stub(monkeypatch):
    # Build stub structure: chromadb + chromadb.utils.embedding_functions
    chromadb_stub = types.ModuleType("chromadb")

    class _Collection:
        def query(self, query_texts, n_results=4):
            return {
                "documents": [[
                    "Mitochondrial genome assembly best practices.",
                    "Quality control guidelines for FASTQ."
                ]],
                "metadatas": [[
                    {"title": "Assembly Best Practices", "source": "https://example.org/asm"},
                    {"title": "QC Guidelines", "source": "https://example.org/qc"}
                ]],
            }

    class _PersistentClient:
        def __init__(self, path):
            self.path = path
        def get_or_create_collection(self, name, metadata=None, embedding_function=None):
            return _Collection()

    chromadb_stub.PersistentClient = _PersistentClient

    # embedding_functions submodule
    emb_mod = types.ModuleType("chromadb.utils.embedding_functions")
    class _SentenceTransformerEmbeddingFunction:
        def __init__(self, model_name):
            self.model_name = model_name
    emb_mod.SentenceTransformerEmbeddingFunction = _SentenceTransformerEmbeddingFunction

    # Install into sys.modules
    sys.modules["chromadb"] = chromadb_stub
    sys.modules["chromadb.utils.embedding_functions"] = emb_mod


def _install_mem0_stub(monkeypatch, store):
    mem0_stub = types.ModuleType("mem0")

    class _Mem0:
        def query(self, params, top_k=3):
            store["query_called"] = True
            store["query_params"] = params
            return [{"text": "previous qc summary", "tags": params.get("tags", [])}]
        def write(self, event):
            store["write_called"] = True
            store["write_event"] = event

    mem0_stub.Mem0 = _Mem0
    sys.modules["mem0"] = mem0_stub


def test_rag_augment_with_stub_chromadb(monkeypatch):
    _install_chromadb_stub(monkeypatch)

    dummy = DummyAgent()
    original = "Check assembly strategy."
    aug, citations = dummy.rag_augment(original, task=None, top_k=2)

    assert aug != original, "Prompt should be augmented when chromadb stub is present"
    assert "参考资料" in aug or "Assembly Best Practices" in aug, "Augmented text should include references"
    assert isinstance(citations, list) and len(citations) >= 1, "Citations should be returned"
    titles = [c.get("title") for c in citations]
    assert "Assembly Best Practices" in titles or "QC Guidelines" in titles


def test_mem0_query_and_write_with_stub(monkeypatch):
    store = {}
    _install_mem0_stub(monkeypatch, store)

    dummy = DummyAgent()
    items = dummy.memory_query(tags=["qc", "R1.fastq"], top_k=2)
    assert items and isinstance(items, list), "mem0 stub should return items"
    assert store.get("query_called") is True, "Mem0.query should be called"

    dummy.memory_write({"agent": "qc", "summary": "score high", "grade": "A"})
    assert store.get("write_called") is True, "Mem0.write should be called"
    assert store.get("write_event", {}).get("agent") == "qc"