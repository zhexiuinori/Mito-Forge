"""
报告生成模块

提供 HTML 报告生成和可视化功能
"""

from .html_generator import generate_html_report
from .visualization import plot_quality_distribution, plot_assembly_stats, plot_annotation_completeness

__all__ = [
    "generate_html_report",
    "plot_quality_distribution",
    "plot_assembly_stats",
    "plot_annotation_completeness"
]
