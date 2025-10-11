"""NanoPlot 输出解析器"""
from pathlib import Path
from typing import Dict, Any, Optional
import re
from .base_parser import BaseOutputParser


class NanoPlotParser(BaseOutputParser):
    """NanoPlot Nanopore数据QC工具输出解析器"""
    
    def find_output_files(self) -> Dict[str, Optional[Path]]:
        """查找 NanoPlot 输出文件"""
        files = {
            'stats': self.output_dir / 'NanoStats.txt',
            'report': self.output_dir / 'NanoPlot-report.html',
            'read_length_plot': self.output_dir / 'LengthvsQualityScatterPlot_dot.png',
            'quality_plot': self.output_dir / 'Non_weightedHistogramReadlength.png'
        }
        
        return {name: path if path.exists() else None for name, path in files.items()}
    
    def parse(self) -> Dict[str, Any]:
        """解析 NanoPlot 输出"""
        files = self.find_output_files()
        
        result = {
            "tool": "nanoplot",
            "version": "unknown",
            "success": files.get('stats') is not None,
            "metrics": {},
            "files": {k: str(v) if v else None for k, v in files.items()},
            "warnings": [],
            "errors": []
        }
        
        # 解析 NanoStats.txt（关键文件）
        if files.get('stats'):
            stats = self._parse_nanostats(files['stats'])
            result['metrics'].update(stats)
        else:
            result['errors'].append("NanoStats.txt not found")
            result['success'] = False
        
        return result
    
    def _parse_nanostats(self, stats_file: Path) -> Dict[str, Any]:
        """
        解析 NanoStats.txt 文件
        
        格式示例:
        Mean read length:                12345.6
        Mean read quality:               12.3
        Median read length:              10000.0
        Median read quality:             11.5
        Number of reads:                 100000
        Read length N50:                 15000
        Total bases:                     1234567890
        """
        metrics = {}
        
        try:
            with open(stats_file, 'r') as f:
                content = f.read()
            
            # 定义需要提取的指标及其正则表达式
            patterns = {
                'mean_read_length': r'Mean read length:\s+([\d.]+)',
                'mean_read_quality': r'Mean read quality:\s+([\d.]+)',
                'median_read_length': r'Median read length:\s+([\d.]+)',
                'median_read_quality': r'Median read quality:\s+([\d.]+)',
                'total_reads': r'Number of reads:\s+(\d+)',
                'n50': r'Read length N50:\s+([\d.]+)',
                'total_bases': r'Total bases:\s+([\d.]+)',
                'gc_content': r'Average percent GC:\s+([\d.]+)',
                'q20_percent': r'>Q20:\s+([\d.]+)',
                'q10_percent': r'>Q10:\s+([\d.]+)',
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, content)
                if match:
                    value = match.group(1)
                    try:
                        # 尝试转换为数值
                        if '.' in value:
                            metrics[key] = float(value)
                        else:
                            metrics[key] = int(value)
                    except ValueError:
                        metrics[key] = value
            
            # 额外计算 avg_length（如果有 mean_read_length）
            if 'mean_read_length' in metrics:
                metrics['avg_length'] = int(metrics['mean_read_length'])
            
            # 额外计算 avg_quality（如果有 mean_read_quality）
            if 'mean_read_quality' in metrics:
                metrics['avg_quality'] = round(metrics['mean_read_quality'], 2)
        
        except Exception:
            pass
        
        return metrics


def parse_nanoplot_output(output_dir: Path) -> Dict[str, Any]:
    """
    便捷函数：解析 NanoPlot 输出目录
    
    Args:
        output_dir: NanoPlot 输出目录
        
    Returns:
        解析后的统计信息字典
    """
    try:
        parser = NanoPlotParser(output_dir)
        return parser.parse()
    except Exception as e:
        return {
            "tool": "nanoplot",
            "version": "unknown",
            "success": False,
            "metrics": {},
            "files": {},
            "warnings": [],
            "errors": [str(e)]
        }
