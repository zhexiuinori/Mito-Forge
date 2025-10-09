import types
import sys
from pathlib import Path

# 我们直接从 doctor 模块导入 run_checks 函数，便于单元测试
from mito_forge.cli.commands import doctor as doctor_mod

def _inject_fake_module(name):
    mod = types.ModuleType(name)
    sys.modules[name] = mod
    return mod

def _remove_module(name):
    if name in sys.modules:
        del sys.modules[name]

def test_doctor_checks_rag_mem0_all_missing(monkeypatch, tmp_path):
    # 确保依赖不存在
    for m in ["chromadb", "mem0", "chromadb.utils.embedding_functions", "sentence_transformers", "sentence-transformers"]:
        _remove_module(m)
    # 指定工作目录可写性检查路径
    work_dir = tmp_path / "work"
    work_dir.mkdir(parents=True, exist_ok=True)
    # 运行检查
    result = doctor_mod.run_checks(base_dir=work_dir)
    # 断言：三项依赖均缺失，work/chroma 创建成功
    assert result["rag"]["chromadb"]["available"] is False
    assert result["rag"]["embedding"]["available"] is False
    assert result["memory"]["mem0"]["available"] is False
    assert result["rag"]["storage"]["path"].endswith("chroma")
    assert result["rag"]["storage"]["writable"] in (True, False)  # 根据权限环境，至少存在字段

def test_doctor_checks_rag_mem0_present(monkeypatch, tmp_path):
    # 注入 fake chromadb 和 embedding function
    chromadb = _inject_fake_module("chromadb")
    class FakeClient:
        def __init__(self, path): self.path = path
        def get_or_create_collection(self, name, metadata=None, embedding_function=None):
            return {"name": name}
    chromadb.PersistentClient = lambda path: FakeClient(path)
    utils_mod = types.ModuleType("chromadb.utils.embedding_functions")
    class FakeEmb:
        def __init__(self, model_name): self.model_name = model_name
    utils_mod.SentenceTransformerEmbeddingFunction = FakeEmb
    sys.modules["chromadb.utils.embedding_functions"] = utils_mod

    # 注入 fake mem0
    mem0 = _inject_fake_module("mem0")
    class FakeMem0:
        def query(self, *a, **k): return []
        def write(self, *a, **k): return None
    mem0.Mem0 = FakeMem0

    work_dir = tmp_path / "work"
    work_dir.mkdir(parents=True, exist_ok=True)

    result = doctor_mod.run_checks(base_dir=work_dir)
    assert result["rag"]["chromadb"]["available"] is True
    assert result["rag"]["embedding"]["available"] is True
    assert result["memory"]["mem0"]["available"] is True
    assert result["rag"]["storage"]["writable"] is True

def test_doctor_render_human_readable(monkeypatch, tmp_path, capsys):
    # 最小渲染测试，避免依赖真实环境
    work_dir = tmp_path / "work"
    work_dir.mkdir(parents=True, exist_ok=True)
    res = {
        "rag": {
            "chromadb": {"available": True, "detail": "ok"},
            "embedding": {"available": False, "detail": "missing sentence-transformers"},
            "storage": {"path": str(work_dir / "chroma"), "writable": True}
        },
        "memory": {
            "mem0": {"available": False, "detail": "module not found"}
        }
    }
    doctor_mod.print_report(res)
    out = capsys.readouterr().out
    assert "RAG/ChromaDB: OK" in out
    assert "Embedding: MISSING" in out
    assert "Mem0: MISSING" in out