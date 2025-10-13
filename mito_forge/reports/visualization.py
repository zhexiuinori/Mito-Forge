"""
可视化模块

生成各种分析图表
"""
import base64
from io import BytesIO
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def plot_quality_distribution(qc_data: Dict[str, Any]) -> Optional[str]:
    """
    绘制质量分布图
    
    Args:
        qc_data: QC 数据
        
    Returns:
        Base64 编码的图片字符串
    """
    try:
        import matplotlib
        matplotlib.use('Agg')  # 使用非交互式后端
        import matplotlib.pyplot as plt
        import numpy as np
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # 质量分数分布
        if 'quality_scores' in qc_data:
            scores = qc_data['quality_scores']
            ax1.hist(scores, bins=50, color='#667eea', alpha=0.7, edgecolor='black')
            ax1.set_xlabel('Quality Score', fontsize=12)
            ax1.set_ylabel('Frequency', fontsize=12)
            ax1.set_title('Quality Score Distribution', fontsize=14, fontweight='bold')
            ax1.grid(True, alpha=0.3)
        
        # 读长分布
        if 'read_lengths' in qc_data:
            lengths = qc_data['read_lengths']
            ax2.hist(lengths, bins=50, color='#764ba2', alpha=0.7, edgecolor='black')
            ax2.set_xlabel('Read Length (bp)', fontsize=12)
            ax2.set_ylabel('Frequency', fontsize=12)
            ax2.set_title('Read Length Distribution', fontsize=14, fontweight='bold')
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 转换为 base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return image_base64
        
    except Exception as e:
        logger.warning(f"Failed to generate quality distribution plot: {e}")
        return None


def plot_assembly_stats(assembly_data: Dict[str, Any]) -> Optional[str]:
    """
    绘制组装统计图
    
    Args:
        assembly_data: 组装数据
        
    Returns:
        Base64 编码的图片字符串
    """
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
        
        # Contig 长度分布
        if 'contig_lengths' in assembly_data:
            lengths = sorted(assembly_data['contig_lengths'], reverse=True)
            ax1.bar(range(len(lengths)), lengths, color='#667eea', alpha=0.7)
            ax1.set_xlabel('Contig Index', fontsize=12)
            ax1.set_ylabel('Length (bp)', fontsize=12)
            ax1.set_title('Contig Length Distribution', fontsize=14, fontweight='bold')
            ax1.grid(True, alpha=0.3)
        
        # N50 图示
        if 'contig_lengths' in assembly_data:
            lengths = sorted(assembly_data['contig_lengths'], reverse=True)
            cumsum = np.cumsum(lengths)
            total = sum(lengths)
            n50_idx = np.where(cumsum >= total / 2)[0][0]
            n50 = lengths[n50_idx]
            
            ax2.plot(range(len(cumsum)), cumsum, color='#764ba2', linewidth=2)
            ax2.axhline(total / 2, color='red', linestyle='--', label=f'50% ({total//2} bp)')
            ax2.axvline(n50_idx, color='green', linestyle='--', label=f'N50 at contig {n50_idx}')
            ax2.set_xlabel('Contig Index', fontsize=12)
            ax2.set_ylabel('Cumulative Length (bp)', fontsize=12)
            ax2.set_title('Cumulative Length & N50', fontsize=14, fontweight='bold')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        
        # 关键指标
        metrics = {
            'N50': assembly_data.get('n50', 0),
            'Total Length': assembly_data.get('total_length', 0),
            'Num Contigs': assembly_data.get('num_contigs', 0),
            'Max Contig': assembly_data.get('max_contig_length', 0)
        }
        
        ax3.axis('off')
        y_pos = 0.8
        for key, value in metrics.items():
            if isinstance(value, int) and value > 1000:
                value_str = f"{value:,} bp" if 'Length' in key or key == 'N50' or key == 'Max Contig' else str(value)
            else:
                value_str = str(value)
            ax3.text(0.1, y_pos, f"{key}:", fontsize=14, fontweight='bold')
            ax3.text(0.6, y_pos, value_str, fontsize=14)
            y_pos -= 0.15
        ax3.set_title('Assembly Metrics', fontsize=14, fontweight='bold')
        
        # GC 含量分布（如果有）
        if 'gc_content' in assembly_data:
            gc_values = assembly_data['gc_content']
            ax4.hist(gc_values, bins=30, color='#4caf50', alpha=0.7, edgecolor='black')
            ax4.set_xlabel('GC Content (%)', fontsize=12)
            ax4.set_ylabel('Frequency', fontsize=12)
            ax4.set_title('GC Content Distribution', fontsize=14, fontweight='bold')
            ax4.grid(True, alpha=0.3)
        else:
            ax4.axis('off')
            ax4.text(0.5, 0.5, 'GC Content\nData Not Available', 
                    ha='center', va='center', fontsize=14, color='gray')
        
        plt.tight_layout()
        
        # 转换为 base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return image_base64
        
    except Exception as e:
        logger.warning(f"Failed to generate assembly stats plot: {e}")
        return None


def plot_annotation_completeness(annotation_data: Dict[str, Any]) -> Optional[str]:
    """
    绘制注释完整度图
    
    Args:
        annotation_data: 注释数据
        
    Returns:
        Base64 编码的图片字符串
    """
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # 基因类型分布（饼图）
        gene_types = {
            'Protein Coding': annotation_data.get('protein_coding', 13),
            'tRNA': annotation_data.get('trna_count', 22),
            'rRNA': annotation_data.get('rrna_count', 2)
        }
        
        colors = ['#667eea', '#764ba2', '#4caf50']
        explode = (0.05, 0.05, 0.05)
        
        ax1.pie(gene_types.values(), labels=gene_types.keys(), autopct='%1.1f%%',
               colors=colors, explode=explode, shadow=True, startangle=90)
        ax1.set_title('Gene Type Distribution', fontsize=14, fontweight='bold')
        
        # 完整度评分（条形图）
        completeness_items = {
            'Overall': annotation_data.get('completeness', 95),
            'Protein Genes': annotation_data.get('protein_completeness', 100),
            'tRNA': annotation_data.get('trna_completeness', 100),
            'rRNA': annotation_data.get('rrna_completeness', 100)
        }
        
        items = list(completeness_items.keys())
        values = list(completeness_items.values())
        colors_bar = ['#667eea', '#764ba2', '#4caf50', '#ff9800']
        
        bars = ax2.barh(items, values, color=colors_bar, alpha=0.7, edgecolor='black')
        ax2.set_xlabel('Completeness (%)', fontsize=12)
        ax2.set_title('Annotation Completeness', fontsize=14, fontweight='bold')
        ax2.set_xlim(0, 100)
        ax2.grid(True, alpha=0.3, axis='x')
        
        # 添加数值标签
        for bar, value in zip(bars, values):
            ax2.text(value + 2, bar.get_y() + bar.get_height()/2, 
                    f'{value}%', va='center', fontsize=10)
        
        plt.tight_layout()
        
        # 转换为 base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return image_base64
        
    except Exception as e:
        logger.warning(f"Failed to generate annotation completeness plot: {e}")
        return None


def plot_polish_comparison(polish_data: Dict[str, Any]) -> Optional[str]:
    """
    绘制抛光前后对比图
    
    Args:
        polish_data: 抛光数据
        
    Returns:
        Base64 编码的图片字符串
    """
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # N50 对比
        categories = ['Original', 'Polished']
        n50_values = [
            polish_data['original']['n50'],
            polish_data['polished']['n50']
        ]
        
        colors = ['#ff9800', '#4caf50']
        bars1 = ax1.bar(categories, n50_values, color=colors, alpha=0.7, edgecolor='black')
        ax1.set_ylabel('N50 (bp)', fontsize=12)
        ax1.set_title('N50 Improvement', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3, axis='y')
        
        # 添加数值标签
        for bar, value in zip(bars1, n50_values):
            ax1.text(bar.get_x() + bar.get_width()/2, value + max(n50_values)*0.02,
                    f'{value:,}', ha='center', va='bottom', fontsize=10)
        
        # 添加改进百分比
        improvement = polish_data.get('n50_change_pct', 0)
        ax1.text(0.5, max(n50_values)*0.5, f'+{improvement:.1f}%',
                ha='center', fontsize=16, fontweight='bold', color='green')
        
        # 总长度对比
        length_values = [
            polish_data['original']['total_length'],
            polish_data['polished']['total_length']
        ]
        
        bars2 = ax2.bar(categories, length_values, color=colors, alpha=0.7, edgecolor='black')
        ax2.set_ylabel('Total Length (bp)', fontsize=12)
        ax2.set_title('Total Length Change', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')
        
        # 添加数值标签
        for bar, value in zip(bars2, length_values):
            ax2.text(bar.get_x() + bar.get_width()/2, value + max(length_values)*0.02,
                    f'{value:,}', ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        
        # 转换为 base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return image_base64
        
    except Exception as e:
        logger.warning(f"Failed to generate polish comparison plot: {e}")
        return None
