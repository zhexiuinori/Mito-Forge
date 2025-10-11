"""Flye 输出解析器"""
from pathlib import Path
from typing import Dict, Any, Optional
import re
from .base_parser import BaseOutputParser, parse_fasta


class FlyeParser(BaseOutputParser):
    """Flye 长读长组装器输出解析器"""
    
    def find_output_files(self) -> Dict[str, Optional[Path]]:
        """查找 Flye 输出文件"""
        files = {
            'assembly': self.output_dir / 'assembly.fasta',
            'assembly_info': self.output_dir / 'assembly_info.txt',
            'assembly_graph': self.output_dir / 'assembly_graph.gfa',
            'assembly_graph_gv': self.output_dir / 'assembly_graph.gv',
            'log': self.output_dir / 'flye.log',
            'params': self.output_dir / 'params.json'
        }
        
        return {name: path if path.exists() else None for name, path in files.items()}
    
    def parse(self) -> Dict[str, Any]:
        """解析 Flye 输出"""
        files = self.find_output_files()
        
        result = {
            "tool": "flye",
            "version": self._parse_version(files.get('log')),
            "success": files.get('assembly') is not None,
            "metrics": {},
            "files": {k: str(v) if v else None for k, v in files.items()},
            "warnings": [],
            "errors": []
        }
        
        # 优先解析 assembly_info.txt (Flye 的关键输出文件)
        if files.get('assembly_info'):
            info_stats = self._parse_assembly_info(files['assembly_info'])
            result['metrics'].update(info_stats)
        
        # 如果没有 assembly_info，则解析 FASTA 文件
        elif files.get('assembly'):
            fasta_stats = parse_fasta(files['assembly'])
            result['metrics'].update({
                'num_contigs': fasta_stats['num_sequences'],
                'total_length': fasta_stats['total_length'],
                'max_contig_length': fasta_stats['max_length'],
                'n50': self._calculate_n50(fasta_stats['lengths']),
                'n90': self._calculate_n90(fasta_stats['lengths']),
            })
            
            # 计算 GC 含量
            gc_content = self._calculate_gc_content(fasta_stats['sequences'])
            result['metrics']['gc_content'] = round(gc_content, 2)
        
        # 解析日志文件
        if files.get('log'):
            log_info = self._parse_log(files['log'])
            result['metrics'].update(log_info)
        
        # 验证
        if result['metrics'].get('num_contigs', 0) == 0:
            result['errors'].append("No contigs assembled")
            result['success'] = False
        
        return result
    
    def _parse_assembly_info(self, info_file: Path) -> Dict[str, Any]:
        """
        解析 Flye 的 assembly_info.txt 文件
        
        格式示例:
        #seq_name       length  cov.    circ.   repeat  mult.   alt_group       graph_path
        contig_1        16569   150.5   Y       N       1       *               *
        """
        metrics = {
            'contigs': [],
            'num_contigs': 0,
            'num_circular': 0,
            'num_repeat': 0,
            'total_length': 0,
            'lengths': [],
            'coverages': []
        }
        
        try:
            with open(info_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) < 4:
                        continue
                    
                    contig_name = parts[0]
                    try:
                        length = int(parts[1])
                        coverage = float(parts[2])
                        is_circular = parts[3] == 'Y' if len(parts) > 3 else False
                        is_repeat = parts[4] == 'Y' if len(parts) > 4 else False
                    except (ValueError, IndexError):
                        continue
                    
                    metrics['contigs'].append({
                        'name': contig_name,
                        'length': length,
                        'coverage': coverage,
                        'circular': is_circular,
                        'repeat': is_repeat
                    })
                    
                    metrics['lengths'].append(length)
                    metrics['coverages'].append(coverage)
                    
                    if is_circular:
                        metrics['num_circular'] += 1
                    if is_repeat:
                        metrics['num_repeat'] += 1
        
        except Exception:
            return metrics
        
        metrics['num_contigs'] = len(metrics['contigs'])
        metrics['total_length'] = sum(metrics['lengths'])
        
        if metrics['lengths']:
            metrics['max_contig_length'] = max(metrics['lengths'])
            metrics['min_contig_length'] = min(metrics['lengths'])
            metrics['n50'] = self._calculate_n50(metrics['lengths'])
            metrics['n90'] = self._calculate_n90(metrics['lengths'])
        
        if metrics['coverages']:
            metrics['average_coverage'] = round(sum(metrics['coverages']) / len(metrics['coverages']), 2)
        
        return metrics
    
    def _parse_version(self, log_file: Optional[Path]) -> str:
        """从日志文件解析 Flye 版本"""
        if not log_file:
            return "unknown"
        
        content = self._read_file_safe(log_file)
        if not content:
            return "unknown"
        
        # 查找版本信息：Flye 2.9.x
        match = re.search(r'Flye\s+(\d+\.\d+(?:\.\d+)?)', content)
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
    
    def _parse_log(self, log_file: Path) -> Dict[str, Any]:
        """解析 Flye 日志文件"""
        info = {}
        
        content = self._read_file_safe(log_file)
        if not content:
            return info
        
        # 查找运行时间
        match = re.search(r'Total\s+time\s+elapsed:\s+([\d.]+)\s+(\w+)', content)
        if match:
            time_val = float(match.group(1))
            unit = match.group(2).lower()
            
            # 转换为秒
            if 'min' in unit:
                info['assembly_time_seconds'] = int(time_val * 60)
            elif 'hour' in unit:
                info['assembly_time_seconds'] = int(time_val * 3600)
            elif 'sec' in unit or 's' == unit:
                info['assembly_time_seconds'] = int(time_val)
        
        return info


def parse_flye_output(output_dir: Path) -> Dict[str, Any]:
    """
    便捷函数：解析 Flye 输出目录
    
    Args:
        output_dir: Flye 输出目录
        
    Returns:
        解析后的统计信息字典
    """
    try:
        parser = FlyeParser(output_dir)
        return parser.parse()
    except Exception as e:
        return {
            "tool": "flye",
            "version": "unknown",
            "success": False,
            "metrics": {},
            "files": {},
            "warnings": [],
            "errors": [str(e)]
        }
