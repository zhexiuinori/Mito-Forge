"""MITOS 输出解析器"""
from pathlib import Path
from typing import Dict, Any, Optional, List
from .base_parser import BaseOutputParser


class MITOSParser(BaseOutputParser):
    """MITOS 线粒体基因组注释工具输出解析器"""
    
    def find_output_files(self) -> Dict[str, Optional[Path]]:
        """查找 MITOS 输出文件"""
        files = {
            'gff': self.output_dir / 'result.gff',
            'bed': self.output_dir / 'result.bed',
            'faa': self.output_dir / 'result.faa',
            'fas': self.output_dir / 'result.fas',
            'mitos': self.output_dir / 'result.mitos',
        }
        
        return {name: path if path.exists() else None for name, path in files.items()}
    
    def parse(self) -> Dict[str, Any]:
        """解析 MITOS 输出"""
        files = self.find_output_files()
        
        result = {
            "tool": "mitos",
            "version": "unknown",
            "success": files.get('gff') is not None,
            "metrics": {},
            "files": {k: str(v) if v else None for k, v in files.items()},
            "warnings": [],
            "errors": []
        }
        
        # 解析 GFF 文件（主要的注释结果）
        if files.get('gff'):
            gff_stats = self._parse_gff(files['gff'])
            result['metrics'].update(gff_stats)
        else:
            result['errors'].append("GFF file not found")
            result['success'] = False
        
        # 解析 BED 文件（额外信息）
        if files.get('bed'):
            bed_stats = self._parse_bed(files['bed'])
            # 如果 GFF 解析失败，使用 BED 作为备用
            if not result['metrics']:
                result['metrics'].update(bed_stats)
        
        return result
    
    def _parse_gff(self, gff_file: Path) -> Dict[str, Any]:
        """
        解析 MITOS GFF3 文件
        
        GFF3 格式:
        seqname  source  feature  start  end  score  strand  frame  attributes
        """
        metrics = {
            'genes': [],
            'trna_count': 0,
            'rrna_count': 0,
            'cds_count': 0,
            'total_genes': 0,
            'gene_types': {}
        }
        
        try:
            with open(gff_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    
                    # 跳过注释和空行
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) < 9:
                        continue
                    
                    seqname = parts[0]
                    feature_type = parts[2]
                    start = parts[3]
                    end = parts[4]
                    strand = parts[6]
                    attributes = parts[8]
                    
                    # 解析属性
                    attrs = self._parse_gff_attributes(attributes)
                    
                    gene_info = {
                        'type': feature_type,
                        'start': int(start),
                        'end': int(end),
                        'strand': strand,
                        'name': attrs.get('Name', attrs.get('ID', 'unknown')),
                        'product': attrs.get('product', ''),
                    }
                    
                    metrics['genes'].append(gene_info)
                    
                    # 统计基因类型
                    if feature_type == 'tRNA':
                        metrics['trna_count'] += 1
                    elif feature_type == 'rRNA':
                        metrics['rrna_count'] += 1
                    elif feature_type == 'CDS':
                        metrics['cds_count'] += 1
                    
                    # 统计所有基因类型
                    if feature_type not in metrics['gene_types']:
                        metrics['gene_types'][feature_type] = 0
                    metrics['gene_types'][feature_type] += 1
        
        except Exception:
            pass
        
        metrics['total_genes'] = len(metrics['genes'])
        
        return metrics
    
    def _parse_gff_attributes(self, attr_string: str) -> Dict[str, str]:
        """
        解析 GFF 属性字符串
        格式: key1=value1;key2=value2
        """
        attrs = {}
        
        for item in attr_string.split(';'):
            item = item.strip()
            if '=' in item:
                key, value = item.split('=', 1)
                attrs[key.strip()] = value.strip()
        
        return attrs
    
    def _parse_bed(self, bed_file: Path) -> Dict[str, Any]:
        """
        解析 BED 文件作为备用
        BED 格式: chrom  start  end  name  score  strand
        """
        metrics = {
            'genes': [],
            'total_genes': 0
        }
        
        try:
            with open(bed_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) < 4:
                        continue
                    
                    gene_info = {
                        'start': int(parts[1]),
                        'end': int(parts[2]),
                        'name': parts[3],
                        'strand': parts[5] if len(parts) > 5 else '+'
                    }
                    
                    metrics['genes'].append(gene_info)
        
        except Exception:
            pass
        
        metrics['total_genes'] = len(metrics['genes'])
        
        return metrics


def parse_mitos_output(output_dir: Path) -> Dict[str, Any]:
    """
    便捷函数：解析 MITOS 输出目录
    
    Args:
        output_dir: MITOS 输出目录
        
    Returns:
        解析后的统计信息字典
    """
    try:
        parser = MITOSParser(output_dir)
        return parser.parse()
    except Exception as e:
        return {
            "tool": "mitos",
            "version": "unknown",
            "success": False,
            "metrics": {},
            "files": {},
            "warnings": [],
            "errors": [str(e)]
        }
