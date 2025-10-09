from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any, Iterable
import re
import hashlib
import os

class _LocalHashEmbeddingFunction:
    """
    本地无网回退嵌入器：
    - 使用 sklearn HashingVectorizer，字符 n-gram，适合中英文混排
    - 无训练、无网络、跨平台稳定
    """
    def __init__(self, n_features: int = 2048):
        try:
            from sklearn.feature_extraction.text import HashingVectorizer
        except Exception as e:
            raise RuntimeError(f"scikit-learn not available for local embedding fallback: {e}")
        self._vec = HashingVectorizer(
            n_features=n_features,
            alternate_sign=False,
            analyzer="char",
            ngram_range=(2, 4),
            norm="l2",
        )

    def __call__(self, input: List[str]) -> List[List[float]]:
        if not input:
            return []
        X = self._vec.transform(input)
        arr = X.toarray().astype("float32")
        return arr.tolist()

    def embed_documents(self, input: List[str]) -> List[List[float]]:
        # 文档向量，输入为字符串列表
        return self.__call__(input)

    def embed_query(self, input):
        # 查询向量，兼容 str 或 List[str]，统一返回 List[List[float]]
        if isinstance(input, str):
            vecs = self.__call__([input])
            return vecs
        elif isinstance(input, list):
            return self.__call__(input)
        else:
            # 非法输入类型，返回空
            return []

    # Chromadb 1.1.x 期望的接口
    def name(self) -> str:
        return "local-hash"

    def is_legacy(self) -> bool:
        # 标记为 legacy 以兼容配置序列化/校验
        return True

def _read_text_file(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")

def _read_pdf_file(p: Path) -> str:
    # 优先使用 pdfplumber，失败回退到 PyPDF2；两者均失败则返回空字符串
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(str(p)) as pdf:
            for page in pdf.pages:
                t = page.extract_text() or ""
                text_parts.append(t)
        return "\n".join(text_parts)
    except Exception:
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(str(p))
            text_parts = []
            for page in reader.pages:
                t = page.extract_text() or ""
                text_parts.append(t)
            return "\n".join(text_parts)
        except Exception:
            return ""

def _normalize_text(s: str) -> str:
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def _chunk_text(text: str, chunk_size: int = 800, chunk_overlap: int = 160) -> List[str]:
    if not text:
        return []
    chunks = []
    start = 0
    n = len(text)
    step = max(1, chunk_size - chunk_overlap)
    while start < n:
        end = min(n, start + chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == n:
            break
        start += step
    return chunks

def _gen_ids(source: str, chunks: List[str]) -> List[str]:
    ids = []
    for i, _ in enumerate(chunks):
        h = hashlib.sha256((source + f"#{i}").encode("utf-8")).hexdigest()[:24]
        ids.append(h)
    return ids

def _iter_files(source_dir: Path) -> Iterable[Path]:
    # 仅遍历一层（data/tool 结构），如需递归可改为 rglob
    for p in source_dir.iterdir():
        if p.is_file() and p.suffix.lower() in {".md", ".txt", ".pdf"}:
            yield p

def _load_embedding():
    """
    嵌入加载优先级（默认无网安全）：
    1) 硅基流动 OpenAI 兼容 Embeddings（需 SILICONFLOW_API_KEY），默认模型 BAAI/bge-m3，可用 SILICONFLOW_EMBEDDING_MODEL 覆盖
    2) 若显式允许（ALLOW_ST_EMBEDDING=1）则使用本地 SentenceTransformer(all-MiniLM-L6-v2)，缓存到 work/models
    3) 否则使用本地 HashingVectorizer 回退（无需网络，默认）
    """
    # 1) SiliconFlow OpenAI-compatible
    try:
        api_key = os.getenv("SILICONFLOW_API_KEY")
        if api_key:
            from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
            model = os.getenv("SILICONFLOW_EMBEDDING_MODEL", "BAAI/bge-m3")
            return OpenAIEmbeddingFunction(
                api_key=api_key,
                model_name=model,
                base_url="https://api.siliconflow.cn/v1",
            )
    except Exception:
        # 忽略并继续回退
        pass

    # 2) 可选：本地 ST（仅在显式允许时启用，避免无网环境触发下载）
    if os.getenv("ALLOW_ST_EMBEDDING") == "1":
        try:
            from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
            cache_dir = Path("work") / "models"
            cache_dir.mkdir(parents=True, exist_ok=True)
            return SentenceTransformerEmbeddingFunction(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                cache_folder=str(cache_dir),
            )
        except Exception:
            pass

    # 3) 默认：离线回退
    return _LocalHashEmbeddingFunction()

def _get_collection(chroma_path: str, collection_name: str, embedding_fn):
    import chromadb
    Path(chroma_path).mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(chroma_path))
    col = client.get_or_create_collection(name=collection_name, embedding_function=embedding_fn)
    return col

def build_vector_db(
    source_dir: str,
    chroma_path: str,
    collection_name: str = "knowledge",
    chunk_size: int = 800,
    chunk_overlap: int = 160,
) -> Dict[str, Any]:
    src = Path(source_dir)
    files = list(_iter_files(src))
    emb = _load_embedding()
    col = _get_collection(chroma_path, collection_name, emb)

    total_chunks = 0
    files_ingested = 0

    for fp in files:
        if fp.suffix.lower() in {".md", ".txt"}:
            raw = _read_text_file(fp)
        else:
            raw = _read_pdf_file(fp)
        text = _normalize_text(raw)
        chunks = _chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        if not chunks:
            continue

        ids = _gen_ids(source=fp.name, chunks=chunks)
        metas = [{"source": fp.name, "chunk_index": i} for i in range(len(chunks))]
        # Chroma 对重复 id 会报错；忽略异常以保持幂等（重复导入不重复写入）
        try:
            col.add(documents=chunks, metadatas=metas, ids=ids)
            files_ingested += 1
            total_chunks += len(chunks)
        except Exception:
            pass

    return {
        "collection": collection_name,
        "chroma_path": str(chroma_path),
        "files_ingested": files_ingested,
        "total_chunks": total_chunks,
    }

def query_collection(
    chroma_path: str,
    collection_name: str,
    queries: List[str],
    n_results: int = 5,
) -> Dict[str, Any]:
    emb = _load_embedding()
    col = _get_collection(chroma_path, collection_name, emb)
    return col.query(query_texts=queries, n_results=n_results)