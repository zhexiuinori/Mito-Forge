"""QUAST 输出解析器"""
from pathlib import Path
from typing import Dict, Any, Optional
from .base_parser import BaseOutputParser


class QUASTParser(BaseOutputParser):
    """QUAST 质量评估工具输出解析器"""
    
    def find_output_files(self) -> Dict[str, Optional[Path]]:
        """查找 QUAST 输出文件"""
        files = {
            'report_txt': self.output_dir / 'report.txt',
            'report_tsv': self.output_dir / 'report.tsv',
            'transposed_report': self.output_dir / 'transposed_report.tsv',
            'report_html': self.output_dir / 'report.html',
            'icarus_html': self.output_dir / 'icarus.html'
        }
        
        return {name: path if path.exists() else None for name, path in files.items()}
    
    def parse(self) -> Dict[str, Any]:
        """解析 QUAST 输出"""
        files = self.find_output_files()
        
        result = {
            "tool": "quast",
            "version": "unknown",
            "success": files.get('report_txt') is not None or files.get('report_tsv') is not None,
            "metrics": {},
            "files": {k: str(v) if v else None for k, v in files.items()},
            "warnings": [],
            "errors": []
        }
        
        # 优先解析 TSV 格式（更结构化）
        if files.get('report_tsv'):
            metrics = self._parse_tsv_report(files['report_tsv'])
            result['metrics'].update(metrics)
        # 否则解析文本格式
        elif files.get('report_txt'):
            metrics = self._parse_txt_report(files['report_txt'])
            result['metrics'].update(metrics)
        else:
            result['errors'].append("No report file found")
            result['success'] = False
        
        return result
    
    def _parse_tsv_report(self, tsv_file: Path) -> Dict[str, Any]:
        """解析 QUAST 的 TSV 报告"""
        metrics = {}
        
        try:
            with open(tsv_file, 'r') as f:
                lines = f.readlines()
            
            if len(lines) < 2:
                return metrics
            
            # 第一行是样本名称
            # 第二行开始是指标
            for line in lines[1:]:
                parts = line.strip().split('\t')
                if len(parts) < 2:
                    continue
                
                metric_name = parts[0].strip()
                metric_value = parts[1].strip()
                
                # 转换为标准化的键名和值
                key, value = self._normalize_metric(metric_name, metric_value)
                if key:
                    metrics[key] = value
        
        except Exception:
            pass
        
        return metrics
    
    def _parse_txt_report(self, txt_file: Path) -> Dict[str, Any]:
        """解析 QUAST 的文本报告"""
        metrics = {}
        
        try:
            with open(txt_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('All statistics'):
                        continue
                    
                    # 格式: metric_name    value
                    if '\t' in line or '  ' in line:
                        parts = line.split(None, 1)  # 按空白分割，最多2部分
                        if len(parts) == 2:
                            metric_name, metric_value = parts
                            key, value = self._normalize_metric(metric_name, metric_value)
                            if key:
                                metrics[key] = value
        
        except Exception:
            pass
        
        return metrics
    
    def _normalize_metric(self, name: str, value: str) -> tuple[Optional[str], Any]:
        """
        标准化指标名称和值
        
        Returns:
            (标准化的键名, 转换后的值) 或 (None, None) 如果无法处理
        """
        # 移除多余空格
        name = name.strip().lower().replace(' ', '_')
        value = value.strip()
        
        # 映射常见指标
        metric_map = {
            '#_contigs': 'num_contigs',
            'largest_contig': 'max_contig_length',
            'total_length': 'total_length',
            'n50': 'n50',
            'n90': 'n90',
            'l50': 'l50',
            'l90': 'l90',
            'gc_(%)': 'gc_content',
            '#_n\'s_per_100_kbp': 'n_per_100kbp',
            'total_length_(>=_0_bp)': 'total_length',
            'total_length_(>=_1000_bp)': 'total_length_ge_1000',
            'total_length_(>=_5000_bp)': 'total_length_ge_5000',
            'total_length_(>=_10000_bp)': 'total_length_ge_10000',
            '#_contigs_(>=_0_bp)': 'num_contigs',
            '#_contigs_(>=_1000_bp)': 'num_contigs_ge_1000',
            '#_contigs_(>=_5000_bp)': 'num_contigs_ge_5000',
            '#_contigs_(>=_10000_bp)': 'num_contigs_ge_10000',
            '#_predicted_genes_(unique)': 'predicted_genes'
        }
        
        # 查找匹配的标准键名
        std_key = metric_map.get(name)
        if not std_key:
            # 如果没有精确匹配，尝试部分匹配
            for pattern, key in metric_map.items():
                if pattern in name:
                    std_key = key
                    break
        
        if not std_key:
            return None, None
        
        # 转换值类型
        try:
            # 尝试转换为整数
            if '.' not in value and value.replace('-', '').isdigit():
                return std_key, int(value)
            # 尝试转换为浮点数
            elif value.replace('.', '').replace('-', '').isdigit():
                return std_key, float(value)
            # 保持字符串
            else:
                return std_key, value
        except ValueError:
            return std_key, value


def parse_quast_output(output_dir: Path) -> Dict[str, Any]:
    """
    便捷函数：解析 QUAST 输出目录
    
    Args:
        output_dir: QUAST 输出目录
        
    Returns:
        解析后的统计信息字典
    """
    try:
        parser = QUASTParser(output_dir)
        return parser.parse()
    except Exception as e:
        return {
            "tool": "quast",
            "version": "unknown",
            "success": False,
            "metrics": {},
            "files": {},
            "warnings": [],
            "errors": [str(e)]
        }
