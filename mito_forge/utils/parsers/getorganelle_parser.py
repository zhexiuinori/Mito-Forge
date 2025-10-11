"""GetOrganelle 输出解析器"""
from pathlib import Path
from typing import Dict, Any, Optional
import re
from .base_parser import BaseOutputParser, parse_fasta


class GetOrganelleParser(BaseOutputParser):
    """GetOrganelle 细胞器基因组组装工具输出解析器"""
    
    def find_output_files(self) -> Dict[str, Optional[Path]]:
        """查找 GetOrganelle 输出文件"""
        files = {}
        
        # 查找路径序列文件 (*.path_sequence.fasta)
        path_seq_files = list(self.output_dir.glob('*.path_sequence.fasta'))
        if path_seq_files:
            files['path_sequence'] = path_seq_files[0]
        else:
            files['path_sequence'] = None
        
        # 查找组装图文件
        graph_files = list(self.output_dir.glob('extended_*.assembly_graph.fastg'))
        if graph_files:
            files['assembly_graph'] = graph_files[0]
        else:
            files['assembly_graph'] = None
        
        # 查找CSV统计文件
        csv_files = list(self.output_dir.glob('extended_*.csv'))
        if csv_files:
            files['csv_stats'] = csv_files[0]
        else:
            files['csv_stats'] = None
        
        # 日志文件
        files['log'] = self.output_dir / 'get_org.log.txt'
        
        return {name: path if (path and path.exists()) else None for name, path in files.items()}
    
    def parse(self) -> Dict[str, Any]:
        """解析 GetOrganelle 输出"""
        files = self.find_output_files()
        
        result = {
            "tool": "getorganelle",
            "version": self._parse_version(files.get('log')),
            "success": files.get('path_sequence') is not None,
            "metrics": {},
            "files": {k: str(v) if v else None for k, v in files.items()},
            "warnings": [],
            "errors": []
        }
        
        # 解析路径序列文件
        if files.get('path_sequence'):
            seq_stats = parse_fasta(files['path_sequence'])
            result['metrics'].update({
                'num_sequences': seq_stats['num_sequences'],
                'total_length': seq_stats['total_length'],
                'max_length': seq_stats['max_length'],
                'min_length': seq_stats['min_length'],
            })
            
            # 计算 GC 含量
            gc_content = self._calculate_gc_content(seq_stats['sequences'])
            result['metrics']['gc_content'] = round(gc_content, 2)
            
            # 检测环状序列（GetOrganelle 通常在头部标记）
            result['metrics']['circular_sequences'] = self._count_circular_sequences(seq_stats['sequences'])
        
        # 解析 CSV 统计文件
        if files.get('csv_stats'):
            csv_stats = self._parse_csv_stats(files['csv_stats'])
            result['metrics'].update(csv_stats)
        
        # 解析日志文件
        if files.get('log'):
            log_info = self._parse_log(files['log'])
            result['metrics'].update(log_info)
        
        # 验证
        if result['metrics'].get('num_sequences', 0) == 0:
            result['errors'].append("No organelle sequences assembled")
            result['success'] = False
        
        return result
    
    def _parse_version(self, log_file: Optional[Path]) -> str:
        """从日志文件解析版本"""
        if not log_file:
            return "unknown"
        
        content = self._read_file_safe(log_file)
        if not content:
            return "unknown"
        
        # GetOrganelle v1.7.x.x
        match = re.search(r'GetOrganelle\s+v?(\d+\.\d+\.\d+(?:\.\d+)?)', content)
        if match:
            return match.group(1)
        
        return "unknown"
    
    def _calculate_gc_content(self, sequences: Dict[str, str]) -> float:
        """计算 GC 含量"""
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
    
    def _count_circular_sequences(self, sequences: Dict[str, str]) -> int:
        """
        统计环状序列数量
        GetOrganelle 通常在序列ID中包含 circular 或 (circular) 标记
        """
        count = 0
        for seq_id in sequences.keys():
            if 'circular' in seq_id.lower():
                count += 1
        return count
    
    def _parse_csv_stats(self, csv_file: Path) -> Dict[str, Any]:
        """
        解析 GetOrganelle 的 CSV 统计文件
        格式: contig_name, length, depth, ...
        """
        stats = {
            'contigs': [],
            'coverages': []
        }
        
        try:
            with open(csv_file, 'r') as f:
                for i, line in enumerate(f):
                    line = line.strip()
                    if not line or i == 0:  # 跳过空行和表头
                        continue
                    
                    parts = line.split(',')
                    if len(parts) < 3:
                        continue
                    
                    try:
                        contig_name = parts[0].strip()
                        length = int(parts[1].strip())
                        depth = float(parts[2].strip())
                        
                        stats['contigs'].append({
                            'name': contig_name,
                            'length': length,
                            'depth': depth
                        })
                        stats['coverages'].append(depth)
                    except (ValueError, IndexError):
                        continue
        
        except Exception:
            pass
        
        if stats['coverages']:
            stats['average_coverage'] = round(sum(stats['coverages']) / len(stats['coverages']), 2)
        
        return stats
    
    def _parse_log(self, log_file: Path) -> Dict[str, Any]:
        """解析 GetOrganelle 日志文件"""
        info = {}
        
        content = self._read_file_safe(log_file)
        if not content:
            return info
        
        # 查找目标类型 (embplant_pt, embplant_mt, etc.)
        match = re.search(r'-F\s+(\w+)', content)
        if match:
            info['target_type'] = match.group(1)
        
        # 查找完成状态
        if 'Result status: finished' in content or 'Result status: successful' in content:
            info['status'] = 'finished'
        elif 'Result status: failed' in content:
            info['status'] = 'failed'
        
        # 查找运行时间
        match = re.search(r'Total\s+running\s+time:\s+([\d.]+)\s*s', content)
        if match:
            info['assembly_time_seconds'] = int(float(match.group(1)))
        
        return info


def parse_getorganelle_output(output_dir: Path) -> Dict[str, Any]:
    """
    便捷函数：解析 GetOrganelle 输出目录
    
    Args:
        output_dir: GetOrganelle 输出目录
        
    Returns:
        解析后的统计信息字典
    """
    try:
        parser = GetOrganelleParser(output_dir)
        return parser.parse()
    except Exception as e:
        return {
            "tool": "getorganelle",
            "version": "unknown",
            "success": False,
            "metrics": {},
            "files": {},
            "warnings": [],
            "errors": [str(e)]
        }
