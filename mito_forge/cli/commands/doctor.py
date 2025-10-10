import click
import os
from pathlib import Path
from ...utils.toolcheck import check_tools, DEFAULT_TOOLS

def run_checks(base_dir: Path | None = None) -> dict:
    """
    检查 RAG/Mem0 相关依赖与存储可写性，返回结构化结果。
    仅做探测，不抛异常，便于单元测试与 CLI 复用。
    """
    base = Path(base_dir) if base_dir else Path.cwd() / "work"
    chroma_dir = base / "chroma"
    res = {
        "rag": {
            "chromadb": {"available": False, "detail": ""},
            "embedding": {"available": False, "detail": ""},
            "storage": {"path": str(chroma_dir), "writable": False},
        },
        "memory": {
            "mem0": {"available": False, "detail": ""},
        },
    }

    # 检查 chromadb 与 embedding
    try:
        import importlib
        chromadb_mod = importlib.import_module("chromadb")
        # embedding 既可能来自 chromadb.utils.embedding_functions，也可能使用 sentence-transformers
        emb_detail = ""
        emb_available = False
        try:
            ef = importlib.import_module("chromadb.utils.embedding_functions")
            _ = getattr(ef, "SentenceTransformerEmbeddingFunction")
            emb_available = True
            emb_detail = "chromadb.utils.embedding_functions OK"
        except Exception as e1:
            # 退化检查 sentence-transformers 是否存在
            try:
                importlib.import_module("sentence_transformers")
                emb_available = True
                emb_detail = "sentence-transformers OK"
            except Exception as e2:
                emb_detail = f"missing sentence-transformers ({e2})"
        res["rag"]["chromadb"]["available"] = True
        res["rag"]["chromadb"]["detail"] = f"chromadb OK: {getattr(chromadb_mod, '__version__', 'unknown')}"
        res["rag"]["embedding"]["available"] = emb_available
        res["rag"]["embedding"]["detail"] = emb_detail
    except Exception as e:
        res["rag"]["chromadb"]["available"] = False
        res["rag"]["chromadb"]["detail"] = f"module not found or init failed: {e}"
        res["rag"]["embedding"]["available"] = False
        res["rag"]["embedding"]["detail"] = "embedding unavailable due to chromadb missing"

    # 检查存储可写
    try:
        chroma_dir.mkdir(parents=True, exist_ok=True)
        test_file = chroma_dir / ".write_test"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("ok")
        test_file.unlink(missing_ok=True)
        res["rag"]["storage"]["writable"] = True
    except Exception:
        res["rag"]["storage"]["writable"] = False

    # 检查 mem0
    try:
        import importlib
        mem0_mod = importlib.import_module("mem0")
        # 进一步探测构造是否可用（不必真的操作后端）
        _Mem0 = getattr(mem0_mod, "Mem0", None)
        if _Mem0 is None:
            raise RuntimeError("mem0.Mem0 not found")
        # 尝试轻量构造（可能会失败，保持容错）
        try:
            _ = _Mem0()
            mem_detail = "Mem0 OK"
            available = True
        except Exception as e:
            mem_detail = f"Mem0 import OK but init failed: {e}"
            available = True  # 认为模块可用，初始化问题交给运行时
        res["memory"]["mem0"]["available"] = available
        res["memory"]["mem0"]["detail"] = mem_detail
    except Exception as e:
        res["memory"]["mem0"]["available"] = False
        res["memory"]["mem0"]["detail"] = f"module not found: {e}"

    return res

def print_report(result: dict) -> None:
    """
    将 run_checks 的结果以人类可读形式输出。
    """
    rag = result.get("rag", {})
    mem = result.get("memory", {})

    chroma_ok = rag.get("chromadb", {}).get("available", False)
    emb_ok = rag.get("embedding", {}).get("available", False)
    storage = rag.get("storage", {})
    mem0_ok = mem.get("mem0", {}).get("available", False)

    click.echo(f"RAG/ChromaDB: {'OK' if chroma_ok else 'MISSING'}")
    click.echo(f"Embedding: {'OK' if emb_ok else 'MISSING'}")
    click.echo(f"RAG Storage: {storage.get('path', '')} (writable={storage.get('writable', False)})")
    click.echo(f"Mem0: {'OK' if mem0_ok else 'MISSING'}")


@click.command("doctor")
@click.option(
    "--tools",
    default=",".join(DEFAULT_TOOLS),
    show_default=True,
    help="Comma-separated external tools to check",
)
def doctor(tools: str):
    """
    检查外部依赖工具是否可用，并给出缺失的安装建议。
    """
    tool_list = [t.strip() for t in tools.split(",") if t.strip()]
    result = check_tools(tool_list)
    present = result["present"]
    missing = result["missing"]

    if present:
        click.echo(f"Present/已安装: {', '.join(present)}")
    else:
        click.echo("Present/已安装: None")

    if missing:
        click.echo(f"Missing/缺失: {', '.join(missing)}")
        click.echo("Suggestions/安装建议:")
        for m in missing:
            detail = result["detail"].get(m, {})
            if not detail.get("found"):
                click.echo(f"- {m}: {detail.get('suggest', 'see bioconda')}")
    else:
        click.echo("Missing/缺失: None")

    click.echo(f"Summary: total={result['summary']['total']}, present={result['summary']['present']}, missing={result['summary']['missing']}")