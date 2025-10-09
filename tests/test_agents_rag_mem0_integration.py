import sys
import types
from pathlib import Path
from mito_forge.core.agents.qc_agent import QCAgent
from mito_forge.core.agents.assembly_agent import AssemblyAgent
from mito_forge.core.agents.annotation_agent import AnnotationAgent
from mito_forge.core.agents.types import TaskSpec
from mito_forge.core.agents.base_agent import BaseAgent

# ----- stubs -----
def install_chromadb_stub():
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

    emb_mod = types.ModuleType("chromadb.utils.embedding_functions")
    class _SentenceTransformerEmbeddingFunction:
        def __init__(self, model_name):
            self.model_name = model_name
    emb_mod.SentenceTransformerEmbeddingFunction = _SentenceTransformerEmbeddingFunction

    sys.modules["chromadb"] = chromadb_stub
    sys.modules["chromadb.utils.embedding_functions"] = emb_mod

def uninstall_chromadb_stub():
    sys.modules.pop("chromadb", None)
    sys.modules.pop("chromadb.utils.embedding_functions", None)

def install_mem0_stub(store):
    mem0_stub = types.ModuleType("mem0")
    class _Mem0:
        def query(self, params, top_k=3):
            store["query_called"] = True
            store["query_params"] = params
            return [{"text": "previous context", "tags": params.get("tags", [])}]
        def write(self, event):
            store["write_called"] = True
            store["write_event"] = event
    mem0_stub.Mem0 = _Mem0
    sys.modules["mem0"] = mem0_stub

def uninstall_mem0_stub():
    sys.modules.pop("mem0", None)

# ----- helpers -----
def make_task(agent_type, inputs, config=None, workdir=None):
    return TaskSpec(
        task_id=f"{agent_type}_tdd",
        agent_type=agent_type,
        inputs=inputs,
        config=(config or {}),
        workdir=str(workdir or Path("work") / f"{agent_type}_tdd")
    )

# ----- tests -----
def test_agents_with_rag_mem0_stubs(tmp_path, monkeypatch):
    # install stubs
    install_chromadb_stub()
    store = {}
    install_mem0_stub(store)

    # hook BaseAgent.memory_write to record calls (without changing business)
    calls = {"count": 0}
    orig_write = BaseAgent.memory_write
    def spy_write(self, event):
        calls["count"] += 1
        calls["last_event"] = event
        return orig_write(self, event)
    monkeypatch.setattr(BaseAgent, "memory_write", spy_write, raising=True)

    # QC
    qc = QCAgent({"threads": 1})
    qc_task = make_task("qc", {"reads": "test.fastq"})
    qc.prepare(Path(tmp_path / "qc"))
    qc_res = qc.run(qc_task.inputs, **qc_task.config)
    ai_qc = qc_res.outputs.get("ai_analysis", {})
    assert isinstance(ai_qc, dict)
    refs_qc = ai_qc.get("references", [])
    assert isinstance(refs_qc, list) and len(refs_qc) >= 1

    # Assembly
    asm = AssemblyAgent({"threads": 1})
    asm_task = make_task("assembly", {"reads": "test.fastq", "assembler": "spades"})
    asm.prepare(Path(tmp_path / "asm"))
    asm_res = asm.run(asm_task.inputs, **asm_task.config)
    ai_asm = asm_res.outputs.get("ai_analysis", {})
    refs_asm = ai_asm.get("references", [])
    assert isinstance(refs_asm, list) and len(refs_asm) >= 1

    # Annotation
    ann = AnnotationAgent({"threads": 1})
    assembly_path = Path(tmp_path / "ann" / "contigs.fasta")
    # 准备存在的组装文件以通过校验
    assembly_path.parent.mkdir(parents=True, exist_ok=True)
    assembly_path.write_text(">contig1ATGCGT", encoding="utf-8")
    ann_task = make_task("annotation", {"assembly": str(assembly_path), "annotator": "mitos"})
    ann.prepare(Path(tmp_path / "ann"))
    ann_res = ann.run(ann_task.inputs, **ann_task.config)
    ai_ann = ann_res.outputs.get("ai_analysis", {})
    refs_ann = ai_ann.get("references", [])
    assert isinstance(refs_ann, list) and len(refs_ann) >= 1

    # memory_write should have been called
    assert calls["count"] >= 3
    last_event = calls.get("last_event", {})
    assert isinstance(last_event, dict)
    assert "agent" in last_event

    # cleanup
    uninstall_chromadb_stub()
    uninstall_mem0_stub()

def test_agents_fallback_without_rag_mem0(tmp_path):
    uninstall_chromadb_stub()
    uninstall_mem0_stub()

    qc = QCAgent({"threads": 1})
    qc_task = make_task("qc", {"reads": "test.fastq"})
    qc.prepare(Path(tmp_path / "qc"))
    qc_res = qc.run(qc_task.inputs, **qc_task.config)
    ai_qc = qc_res.outputs.get("ai_analysis", {})
    assert isinstance(ai_qc, dict)
    assert ai_qc.get("references", []) in ([], None)

    asm = AssemblyAgent({"threads": 1})
    asm_task = make_task("assembly", {"reads": "test.fastq", "assembler": "spades"})
    asm.prepare(Path(tmp_path / "asm"))
    asm_res = asm.run(asm_task.inputs, **asm_task.config)
    ai_asm = asm_res.outputs.get("ai_analysis", {})
    assert ai_asm.get("references", []) in ([], None)

    ann = AnnotationAgent({"threads": 1})
    ann_task = make_task("annotation", {"assembly_file": "contigs.fasta", "tool": "mitos"})
    ann.prepare(Path(tmp_path / "ann"))
    ann_res = ann.run(ann_task.inputs, **ann_task.config)
    ai_ann = ann_res.outputs.get("ai_analysis", {})
    assert ai_ann.get("references", []) in ([], None)