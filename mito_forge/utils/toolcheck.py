"""
外部工具检测工具集
"""
from __future__ import annotations
from typing import List, Dict, Any
from pathlib import Path
import shutil


DEFAULT_TOOLS = [
    # Assembly tools
    "spades", "flye", "unicycler", 
    # QC tools
    "fastqc", "nanoplot",
    # Polishing tools
    "pilon", "racon", "medaka",
    # Mapping tools
    "minimap2",
    # Mitochondrial-specific tools
    "pmat2", "getorganelle", "novoplasty",
    # Annotation tools
    "mitos", "blast",
    # Quality assessment
    "quast"
]


def suggest_installation(name: str) -> str:
    # 提供跨平台的通用安装建议（不执行）
    suggestions = {
        # Assembly tools
        "spades": "Install SPAdes from https://github.com/ablab/spades or bioconda: conda install -c bioconda spades",
        "flye": "Install Flye via bioconda: conda install -c bioconda flye",
        "unicycler": "Install Unicycler via bioconda: conda install -c bioconda unicycler",
        # QC tools
        "fastqc": "Install FastQC via bioconda: conda install -c bioconda fastqc",
        "nanoplot": "Install NanoPlot via bioconda: conda install -c bioconda nanoplot",
        "trimmomatic": "Install Trimmomatic via bioconda: conda install -c bioconda trimmomatic",
        "cutadapt": "Install cutadapt via bioconda: conda install -c bioconda cutadapt",
        # Polishing tools
        "pilon": "Install Pilon (Java) via bioconda: conda install -c bioconda pilon",
        "racon": "Install racon via bioconda: conda install -c bioconda racon",
        "medaka": "Install medaka via bioconda: conda install -c bioconda medaka",
        # Mapping tools
        "minimap2": "Install minimap2 via bioconda: conda install -c bioconda minimap2",
        # Mitochondrial-specific tools
        "pmat2": "Install via project tools manager: doctor --fix, or from https://github.com/aiPGAB/PMAT2",
        "getorganelle": "Install via project tools manager: doctor --fix, or from https://github.com/Kinggerm/GetOrganelle",
        "novoplasty": "Install via project tools manager: doctor --fix, or from https://github.com/ndierckx/NOVOPlasty",
        # Annotation tools
        "mitos": "Install MITOS via bioconda: conda install -c bioconda mitos",
        "blast": "Install BLAST+ via bioconda: conda install -c bioconda blast",
        "hmmer": "Install HMMER via bioconda: conda install -c bioconda hmmer",
        # Quality assessment
        "quast": "Install QUAST via bioconda: conda install -c bioconda quast",
    }
    return suggestions.get(name, f"Search installation guide for {name} (bioconda recommended).")


def check_tools(tools: List[str] | None = None, project_root: Path | None = None) -> Dict[str, Any]:
    tools = tools or DEFAULT_TOOLS
    present = []
    missing = []
    detail = {}
    
    # 确定项目根目录
    if project_root is None:
        project_root = Path.cwd()
    
    for t in tools:
        # 先检查系统 PATH
        path = shutil.which(t)
        
        # 如果系统 PATH 没找到，检查项目本地工具目录
        if not path:
            from .tools_manager import ToolsManager
            try:
                tm = ToolsManager(project_root=project_root)
                local_path = tm.where(t)
                if local_path and Path(local_path).exists():
                    path = local_path
            except Exception:
                pass
        
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