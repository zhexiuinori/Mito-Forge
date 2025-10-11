"""解析器基类"""
from pathlib import Path
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod


class BaseOutputParser(ABC):
    """所有工具输出解析器的基类"""
    
    def __init__(self, output_dir: Path):
        """
        Args:
            output_dir: 工具的输出目录
        """
        self.output_dir = Path(output_dir)
        if not self.output_dir.exists():
            raise FileNotFoundError(f"Output directory not found: {output_dir}")
    
    @abstractmethod
    def find_output_files(self) -> Dict[str, Optional[Path]]:
        """
        查找工具的输出文件
        
        Returns:
            文件名到路径的映射，如果文件不存在则为 None
        """
        pass
    
    @abstractmethod
    def parse(self) -> Dict[str, Any]:
        """
        解析输出文件
        
        Returns:
            标准化的解析结果字典
        """
        pass
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        验证输出文件是否完整
        
        Returns:
            (是否有效, 错误消息列表)
        """
        files = self.find_output_files()
        errors = []
        
        for name, path in files.items():
            if path is None:
                errors.append(f"Missing output file: {name}")
            elif not path.exists():
                errors.append(f"Output file not found: {name} at {path}")
        
        return len(errors) == 0, errors
    
    def _read_file_safe(self, filepath: Path, encoding: str = 'utf-8') -> Optional[str]:
        """
        安全地读取文件内容
        
        Args:
            filepath: 文件路径
            encoding: 编码方式
            
        Returns:
            文件内容，如果失败返回 None
        """
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
        except Exception:
            return None
    
    def _calculate_n50(self, lengths: List[int]) -> int:
        """
        计算 N50
        
        Args:
            lengths: 序列长度列表
            
        Returns:
            N50 值
        """
        if not lengths:
            return 0
        
        sorted_lengths = sorted(lengths, reverse=True)
        total_length = sum(sorted_lengths)
        target = total_length / 2
        
        cumulative = 0
        for length in sorted_lengths:
            cumulative += length
            if cumulative >= target:
                return length
        
        return sorted_lengths[0]
    
    def _calculate_n90(self, lengths: List[int]) -> int:
        """计算 N90"""
        if not lengths:
            return 0
        
        sorted_lengths = sorted(lengths, reverse=True)
        total_length = sum(sorted_lengths)
        target = total_length * 0.9
        
        cumulative = 0
        for length in sorted_lengths:
            cumulative += length
            if cumulative >= target:
                return length
        
        return sorted_lengths[-1]


def parse_fasta(fasta_file: Path) -> Dict[str, Any]:
    """
    解析 FASTA 文件，提取基本统计信息
    
    Args:
        fasta_file: FASTA 文件路径
        
    Returns:
        包含序列统计信息的字典
    """
    if not fasta_file.exists():
        return {
            "num_sequences": 0,
            "total_length": 0,
            "lengths": [],
            "sequences": {}
        }
    
    sequences = {}
    current_id = None
    current_seq = []
    
    with open(fasta_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('>'):
                # 保存前一个序列
                if current_id is not None:
                    sequences[current_id] = ''.join(current_seq)
                
                # 开始新序列
                current_id = line[1:].split()[0]  # 取第一个空格前的部分作为ID
                current_seq = []
            else:
                current_seq.append(line)
        
        # 保存最后一个序列
        if current_id is not None:
            sequences[current_id] = ''.join(current_seq)
    
    lengths = [len(seq) for seq in sequences.values()]
    
    return {
        "num_sequences": len(sequences),
        "total_length": sum(lengths),
        "lengths": lengths,
        "sequences": sequences,
        "max_length": max(lengths) if lengths else 0,
        "min_length": min(lengths) if lengths else 0,
        "mean_length": sum(lengths) / len(lengths) if lengths else 0
    }
