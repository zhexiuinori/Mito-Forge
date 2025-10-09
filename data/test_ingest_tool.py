import sys
from pathlib import Path
import importlib
import pytest

DATA_DIR = Path(__file__).parent
PROJECT_ROOT = DATA_DIR.parent
SOURCE_DIR = DATA_DIR / "tool"
CHROMA_DIR = PROJECT_ROOT / "work" / "chroma"

# 跳过条件：缺少关键依赖时跳过（便于TDD在未安装依赖时不误报）
try:
    import chromadb  # noqa: F401
    _HAS_CHROMA = True
except Exception:
    _HAS_CHROMA = False

try:
    import sentence_transformers  # noqa: F401
    _HAS_SENT = True
except Exception:
    _HAS_SENT = False

pytestmark = [
    pytest.mark.skipif(not _HAS_CHROMA, reason="chromadb not installed"),
    pytest.mark.skipif(not _HAS_SENT, reason="sentence-transformers not installed"),
]


def test_data_tool_dir_exists_and_has_files():
    assert SOURCE_DIR.exists(), f"Missing dir: {SOURCE_DIR}"
    files = [p for p in SOURCE_DIR.iterdir() if p.is_file() and p.suffix.lower() in {".md", ".txt", ".pdf"}]
    assert len(files) > 0, "data/tool 下应至少有一个 .md/.txt/.pdf 文件"


@pytest.mark.parametrize("query", ["BLAST", "SPAdes", "Flye"])
def test_ingest_tool_dir_and_query(query):
    # 导入实现
    sys.path.insert(0, str(DATA_DIR))
    ing = importlib.import_module("ingest_data")

    # 执行构建：从 data/tool 读文件，写入项目 work/chroma
    info = ing.build_vector_db(
        source_dir=str(SOURCE_DIR),
        chroma_path=str(CHROMA_DIR),
        collection_name="knowledge",
        chunk_size=800,
        chunk_overlap=160,
    )
    assert Path(info["chroma_path"]).exists()
    assert info["files_ingested"] >= 1
    assert info["total_chunks"] >= 1

    # 查询验证（不强制包含关键词，仅验证可召回）
    res = ing.query_collection(
        chroma_path=str(CHROMA_DIR),
        collection_name="knowledge",
        queries=[query],
        n_results=5,
    )
    assert isinstance(res, dict)
    assert "documents" in res and res["documents"] and len(res["documents"][0]) >= 1
    assert "metadatas" in res and res["metadatas"] and len(res["metadatas"][0]) >= 1
    assert "source" in res["metadatas"][0][0]