"""SPAdes 输出解析器"""
from pathlib import Path
from typing import Dict, Any, Optional
import re
from .base_parser import BaseOutputParser, parse_fasta


class SPAdesParser(BaseOutputParser):
    """SPAdes 组装器输出解析器"""
    
    def find_output_files(self) -> Dict[str, Optional[Path]]:
        """查找 SPAdes 输出文件"""
        files = {
            'contigs': self.output_dir / 'contigs.fasta',
            'scaffolds': self.output_dir / 'scaffolds.fasta',
            'assembly_graph': self.output_dir / 'assembly_graph.fastg',
            'contigs_paths': self.output_dir / 'contigs.paths',
            'scaffolds_paths': self.output_dir / 'scaffolds.paths',
            'log': self.output_dir / 'spades.log',
            'params': self.output_dir / 'params.txt'
        }
        
        # 检查文件是否存在
        return {name: path if path.exists() else None for name, path in files.items()}
    
    def parse(self) -> Dict[str, Any]:
        """解析 SPAdes 输出"""
        files = self.find_output_files()
        
        result = {
            "tool": "spades",
            "version": self._parse_version(files.get('log')),
            "success": files.get('contigs') is not None,
            "metrics": {},
            "files": {k: str(v) if v else None for k, v in files.items()},
            "warnings": [],
            "errors": []
        }
        
        # 解析 contigs
        if files.get('contigs'):
            contig_stats = parse_fasta(files['contigs'])
            result['metrics'].update({
                'num_contigs': contig_stats['num_sequences'],
                'total_length': contig_stats['total_length'],
                'max_contig_length': contig_stats['max_length'],
                'min_contig_length': contig_stats['min_length'],
                'mean_contig_length': int(contig_stats['mean_length']),
                'n50': self._calculate_n50(contig_stats['lengths']),
                'n90': self._calculate_n90(contig_stats['lengths']),
            })
            
            # 计算 GC 含量
            gc_content = self._calculate_gc_content(contig_stats['sequences'])
            result['metrics']['gc_content'] = round(gc_content, 2)
            
            # 从 contig 名称解析覆盖度信息
            coverage_info = self._parse_coverage_from_headers(contig_stats['sequences'])
            if coverage_info:
                result['metrics']['average_coverage'] = round(coverage_info['mean_coverage'], 2)
        
        # 解析日志文件获取额外信息
        if files.get('log'):
            log_info = self._parse_log(files['log'])
            result['metrics'].update(log_info)
        
        # 验证结果
        if result['metrics'].get('num_contigs', 0) == 0:
            result['errors'].append("No contigs assembled")
            result['success'] = False
        
        return result
    
    def _parse_version(self, log_file: Optional[Path]) -> str:
        """从日志文件解析 SPAdes 版本"""
        if not log_file:
            return "unknown"
        
        content = self._read_file_safe(log_file)
        if not content:
            return "unknown"
        
        # 查找版本信息：SPAdes v3.15.5
        match = re.search(r'SPAdes\s+v?(\d+\.\d+\.\d+)', content)
        if match:
            return match.group(1)
        
        return "unknown"
    
    def _calculate_gc_content(self, sequences: Dict[str, str]) -> float:
        """计算 GC 含量百分比"""
        if not sequences:
            return 0.0
        
        total_bases = 0
        gc_bases = 0
        
        for seq in sequences.values():
            seq_upper = seq.upper()
            total_bases += len(seq_upper)
            gc_bases += seq_upper.count('G') + seq_upper.count('C')
        
        if total_bases == 0:
            return 0.0
        
        return (gc_bases / total_bases) * 100
    
    def _parse_coverage_from_headers(self, sequences: Dict[str, str]) -> Optional[Dict[str, float]]:
        """
        从 SPAdes contig 头部解析覆盖度信息
        格式例如: NODE_1_length_16569_cov_150.123
        """
        coverages = []
        
        for header in sequences.keys():
            # 匹配 cov_XXX.XXX 模式
            match = re.search(r'cov_(\d+\.?\d*)', header)
            if match:
                try:
                    cov = float(match.group(1))
                    coverages.append(cov)
                except ValueError:
                    continue
        
        if not coverages:
            return None
        
        return {
            'mean_coverage': sum(coverages) / len(coverages),
            'min_coverage': min(coverages),
            'max_coverage': max(coverages)
        }
    
    def _parse_log(self, log_file: Path) -> Dict[str, Any]:
        """解析 SPAdes 日志文件获取额外信息"""
        info = {}
        
        content = self._read_file_safe(log_file)
        if not content:
            return info
        
        # 查找运行时间
        match = re.search(r'Total\s+time:\s+(\d+)\s+hours\s+(\d+)\s+min\s+(\d+\.\d+)\s+sec', content)
        if match:
            hours, mins, secs = float(match.group(1)), float(match.group(2)), float(match.group(3))
            info['assembly_time_seconds'] = int(hours * 3600 + mins * 60 + secs)
        
        # 查找使用的 k-mer 大小
        k_mers = re.findall(r'K\s*=\s*(\d+)', content)
        if k_mers:
            info['k_mers_used'] = [int(k) for k in k_mers]
        
        return info


def parse_spades_output(output_dir: Path) -> Dict[str, Any]:
    """
    便捷函数：解析 SPAdes 输出目录
    
    Args:
        output_dir: SPAdes 输出目录
        
    Returns:
        解析后的统计信息字典
    """
    try:
        parser = SPAdesParser(output_dir)
        return parser.parse()
    except Exception as e:
        return {
            "tool": "spades",
            "version": "unknown",
            "success": False,
            "metrics": {},
            "files": {},
            "warnings": [],
            "errors": [str(e)]
        }
