"""
外部工具检测工具集
"""
from __future__ import annotations
from typing import List, Dict, Any
import shutil


DEFAULT_TOOLS = ["spades", "flye", "pilon", "racon", "medaka", "minimap2"]


def suggest_installation(name: str) -> str:
    # 提供跨平台的通用安装建议（不执行）
    suggestions = {
        "spades": "Install SPAdes from https://github.com/ablab/spades or bioconda: conda install -c bioconda spades",
        "flye": "Install Flye via bioconda: conda install -c bioconda flye",
        "pilon": "Install Pilon (Java) via bioconda: conda install -c bioconda pilon",
        "racon": "Install racon via bioconda: conda install -c bioconda racon",
        "medaka": "Install medaka via bioconda: conda install -c bioconda medaka",
        "minimap2": "Install minimap2 via bioconda: conda install -c bioconda minimap2",
    }
    return suggestions.get(name, f"Search installation guide for {name} (bioconda recommended).")


def check_tools(tools: List[str] | None = None) -> Dict[str, Any]:
    tools = tools or DEFAULT_TOOLS
    present = []
    missing = []
    detail = {}
    for t in tools:
        path = shutil.which(t)
        if path:
            present.append(t)
            detail[t] = {"found": True, "path": path}
        else:
            missing.append(t)
            detail[t] = {"found": False, "suggest": suggest_installation(t)}
    return {
        "present": present,
        "missing": missing,
        "detail": detail,
        "summary": {
            "total": len(tools),
            "present": len(present),
            "missing": len(missing),
        },
    }