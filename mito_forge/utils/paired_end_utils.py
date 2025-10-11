"""
双端测序数据处理辅助函数
"""
from pathlib import Path
from typing import Optional, Dict, Any


def detect_paired_end(reads_path: str) -> Optional[str]:
    """
    自动检测双端数据的 R2 文件
    
    Args:
        reads_path: R1 文件路径
        
    Returns:
        R2 文件路径，如果找不到则返回 None
        
    Examples:
        >>> detect_paired_end("sample_R1_001.fastq.gz")
        "sample_R2_001.fastq.gz"
        >>> detect_paired_end("data_1.fq")
        "data_2.fq"
    """
    p = Path(reads_path)
    
    # 常见的双端测序命名模式
    patterns = [
        ("_R1_", "_R2_"),
        ("_R1.", "_R2."),
        ("_1.", "_2."),
        (".R1.", ".R2."),
        ("_1_", "_2_"),
        ("_forward", "_reverse"),
        ("_fwd", "_rev"),
        (".1.", ".2."),
    ]
    
    for pat1, pat2 in patterns:
        if pat1 in p.name:
            r2_name = p.name.replace(pat1, pat2)
            r2_path = p.parent / r2_name
            if r2_path.exists():
                return str(r2_path)
    
    return None


def merge_paired_qc_metrics(r1_metrics: Dict[str, Any], r2_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    合并 R1 和 R2 的 QC 指标
    
    Args:
        r1_metrics: R1 的 QC 指标
        r2_metrics: R2 的 QC 指标
        
    Returns:
        合并后的指标字典
    """
    # 计算总和
    total_reads = r1_metrics.get("total_reads", 0) + r2_metrics.get("total_reads", 0)
    
    # 计算平均值
    avg_quality = (r1_metrics.get("avg_quality", 0) + r2_metrics.get("avg_quality", 0)) / 2
    avg_length = (r1_metrics.get("avg_read_length", 0) + r2_metrics.get("avg_read_length", 0)) / 2
    gc_content = (r1_metrics.get("gc_content", 0) + r2_metrics.get("gc_content", 0)) / 2
    
    # 使用最差的质量作为整体质量（保守估计）
    overall_quality = min(
        r1_metrics.get("overall_quality", 1.0),
        r2_metrics.get("overall_quality", 1.0)
    )
    
    return {
        "paired_end": True,
        "total_reads": total_reads,
        "avg_quality": avg_quality,
        "avg_read_length": avg_length,
        "gc_content": gc_content,
        "overall_quality": overall_quality,
        # 保留单独的 R1 和 R2 质量
        "r1_quality": r1_metrics.get("overall_quality", 1.0),
        "r2_quality": r2_metrics.get("overall_quality", 1.0),
        "r1_reads": r1_metrics.get("total_reads", 0),
        "r2_reads": r2_metrics.get("total_reads", 0),
    }


def validate_paired_reads(reads1: str, reads2: str) -> Dict[str, Any]:
    """
    验证双端测序文件是否匹配
    
    Args:
        reads1: R1 文件路径
        reads2: R2 文件路径
        
    Returns:
        验证结果字典，包含 valid (bool) 和 warnings (list)
    """
    warnings = []
    
    p1 = Path(reads1)
    p2 = Path(reads2)
    
    # 检查文件是否存在
    if not p1.exists():
        return {"valid": False, "warnings": [f"R1 文件不存在: {reads1}"]}
    if not p2.exists():
        return {"valid": False, "warnings": [f"R2 文件不存在: {reads2}"]}
    
    # 检查文件大小是否相近（允许 20% 差异）
    size1 = p1.stat().st_size
    size2 = p2.stat().st_size
    
    if size1 > 0 and size2 > 0:
        size_ratio = max(size1, size2) / min(size1, size2)
        if size_ratio > 1.2:
            warnings.append(
                f"R1 和 R2 文件大小差异较大: R1={size1//1024//1024}MB, R2={size2//1024//1024}MB"
            )
    
    # 检查文件扩展名是否一致
    if p1.suffix != p2.suffix:
        warnings.append(
            f"R1 和 R2 文件扩展名不一致: {p1.suffix} vs {p2.suffix}"
        )
    
    return {
        "valid": True,
        "warnings": warnings,
        "size_r1_mb": size1 // 1024 // 1024,
        "size_r2_mb": size2 // 1024 // 1024,
    }
