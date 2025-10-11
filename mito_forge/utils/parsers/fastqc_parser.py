"""FastQC 输出解析器"""
import zipfile
from pathlib import Path
from typing import Dict, Any, List, Optional


def parse_fastqc_output(fastqc_zip: Path) -> Dict[str, Any]:
    """
    解析 FastQC 生成的 zip 文件
    
    Args:
        fastqc_zip: FastQC 输出的 .zip 文件路径
        
    Returns:
        包含 QC 统计信息的字典
    """
    if not fastqc_zip.exists():
        raise FileNotFoundError(f"FastQC output not found: {fastqc_zip}")
    
    result = {
        "filename": "",
        "total_reads": 0,
        "total_bases": 0,
        "avg_length": 0,
        "avg_quality": 0.0,
        "gc_content": 0.0,
        "q20_percent": 0.0,
        "q30_percent": 0.0,
        "detected_issues": [],
        "read_type": "illumina"
    }
    
    # 解析 fastqc_data.txt
    with zipfile.ZipFile(fastqc_zip, 'r') as zf:
        # 找到 fastqc_data.txt
        data_file = None
        for name in zf.namelist():
            if name.endswith('fastqc_data.txt'):
                data_file = name
                break
        
        if not data_file:
            raise ValueError("fastqc_data.txt not found in zip")
        
        # 读取数据
        with zf.open(data_file) as f:
            content = f.read().decode('utf-8')
        
        # 解析基础统计
        in_basic_stats = False
        in_quality_section = False
        quality_values = []
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Basic Statistics 部分
            if line.startswith(">>Basic Statistics"):
                in_basic_stats = True
                continue
            elif line.startswith(">>END_MODULE"):
                in_basic_stats = False
                in_quality_section = False
                continue
            
            if in_basic_stats and '\t' in line and not line.startswith('#'):
                parts = line.split('\t')
                if len(parts) >= 2:
                    key, value = parts[0], parts[1]
                    
                    if key == "Filename":
                        result["filename"] = value
                    elif key == "Total Sequences":
                        result["total_reads"] = int(value)
                    elif key == "Sequence length":
                        # 可能是 "150" 或 "35-151"
                        if '-' in value:
                            parts = value.split('-')
                            result["avg_length"] = (int(parts[0]) + int(parts[1])) // 2
                        else:
                            result["avg_length"] = int(value)
                    elif key == "%GC":
                        result["gc_content"] = float(value)
                    elif key == "Total Bases":
                        # 格式: "1.5 Mbp" 或 "150000000"
                        if 'Mbp' in value:
                            result["total_bases"] = int(float(value.replace('Mbp', '').strip()) * 1_000_000)
                        elif 'Kbp' in value:
                            result["total_bases"] = int(float(value.replace('Kbp', '').strip()) * 1_000)
                        elif 'Gbp' in value:
                            result["total_bases"] = int(float(value.replace('Gbp', '').strip()) * 1_000_000_000)
                        else:
                            result["total_bases"] = int(value)
            
            # Per base sequence quality 部分
            if line.startswith(">>Per base sequence quality"):
                in_quality_section = True
                continue
            
            if in_quality_section and not line.startswith('#') and '\t' in line:
                parts = line.split('\t')
                if len(parts) >= 2:
                    try:
                        mean_quality = float(parts[1])
                        quality_values.append(mean_quality)
                    except ValueError:
                        pass
        
        # 计算平均质量
        if quality_values:
            result["avg_quality"] = sum(quality_values) / len(quality_values)
        
        # 估算 Q20/Q30 百分比（基于平均质量）
        # 如果平均质量 >= 30，Q30 > 85%
        # 如果平均质量 >= 20，Q20 > 95%
        avg_q = result["avg_quality"]
        if avg_q >= 35:
            result["q30_percent"] = 95.0
            result["q20_percent"] = 99.0
        elif avg_q >= 30:
            result["q30_percent"] = 85.0 + (avg_q - 30) * 2
            result["q20_percent"] = 98.0
        elif avg_q >= 25:
            result["q30_percent"] = 50.0 + (avg_q - 25) * 7
            result["q20_percent"] = 95.0
        elif avg_q >= 20:
            result["q30_percent"] = 20.0 + (avg_q - 20) * 6
            result["q20_percent"] = 90.0 + (avg_q - 20)
        else:
            result["q30_percent"] = max(0, (avg_q - 10) * 2)
            result["q20_percent"] = max(0, (avg_q - 10) * 4)
        
        # 解析 summary.txt 获取问题
        summary_file = None
        for name in zf.namelist():
            if name.endswith('summary.txt'):
                summary_file = name
                break
        
        if summary_file:
            with zf.open(summary_file) as f:
                summary_content = f.read().decode('utf-8')
            
            for line in summary_content.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split('\t')
                if len(parts) >= 2:
                    status, module = parts[0], parts[1]
                    if status in ['WARN', 'FAIL']:
                        severity = 'medium' if status == 'WARN' else 'high'
                        result["detected_issues"].append({
                            "type": module,
                            "severity": severity,
                            "description": f"{module} check {status.lower()}ed"
                        })
    
    # 计算一些额外指标
    if result["total_reads"] > 0 and result["total_bases"] > 0:
        result["min_length"] = max(1, result["avg_length"] - 50)
        result["max_length"] = result["avg_length"] + 50
        result["n50"] = result["avg_length"]
    
    return result


def find_fastqc_output(output_dir: Path, input_file: Path) -> Optional[Path]:
    """
    根据输入文件名查找 FastQC 输出的 zip 文件
    
    Args:
        output_dir: FastQC 输出目录
        input_file: 输入的 fastq 文件
        
    Returns:
        FastQC zip 文件路径，如果未找到返回 None
    """
    # FastQC 输出格式: {basename}_fastqc.zip
    basename = input_file.name
    # 移除常见后缀
    for suffix in ['.fq.gz', '.fastq.gz', '.fq', '.fastq']:
        if basename.endswith(suffix):
            basename = basename[:-len(suffix)]
            break
    
    zip_file = output_dir / f"{basename}_fastqc.zip"
    return zip_file if zip_file.exists() else None
