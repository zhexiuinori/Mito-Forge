"""
HTML 报告生成器

使用 Jinja2 模板生成完整的 HTML 报告
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def generate_html_report(
    state: Dict[str, Any],
    output_path: Path,
    template_path: Optional[Path] = None
) -> Path:
    """
    生成 HTML 报告
    
    Args:
        state: Pipeline 状态
        output_path: 输出文件路径
        template_path: 模板文件路径（可选）
        
    Returns:
        生成的 HTML 文件路径
    """
    try:
        from jinja2 import Template, Environment, FileSystemLoader
        
        # 准备模板数据
        template_data = _prepare_template_data(state)
        
        # 加载模板
        if template_path and template_path.exists():
            env = Environment(loader=FileSystemLoader(template_path.parent))
            template = env.get_template(template_path.name)
        else:
            # 使用默认模板
            default_template_path = Path(__file__).parent / "templates" / "report.html"
            if default_template_path.exists():
                with open(default_template_path, 'r', encoding='utf-8') as f:
                    template = Template(f.read())
            else:
                # 使用简单的回退模板
                template = Template(_get_fallback_template())
        
        # 渲染模板
        html_content = template.render(**template_data)
        
        # 写入文件
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML report generated: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to generate HTML report: {e}")
        # 生成简单的错误报告
        return _generate_error_report(state, output_path, str(e))


def _prepare_template_data(state: Dict[str, Any]) -> Dict[str, Any]:
    """准备模板数据"""
    from .visualization import (
        plot_quality_distribution,
        plot_assembly_stats,
        plot_annotation_completeness,
        plot_polish_comparison
    )
    
    # 基本信息
    data = {
        'pipeline_id': state.get('pipeline_id', 'unknown'),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_time': _format_duration(state.get('end_time', 0) - state.get('start_time', 0)),
        'read_type': state.get('config', {}).get('detected_read_type', 'unknown'),
        'kingdom': state.get('config', {}).get('kingdom', 'unknown'),
        'pipeline_status': 'completed' if state.get('done') else 'running'
    }
    
    # 阶段信息
    stages_info = []
    total_stages = 0
    completed_stages = 0
    
    for stage_name in ['supervisor', 'qc', 'assembly', 'polish', 'annotation', 'report']:
        status = state.get('stage_status', {}).get(stage_name, 'pending')
        if status != 'pending':
            total_stages += 1
            if status == 'completed':
                completed_stages += 1
        
        stage_metrics = state.get('stage_metrics', {}).get(stage_name, {})
        duration = _format_duration(stage_metrics.get('duration', 0))
        
        stage_info = {
            'name': stage_name.capitalize(),
            'status': status,
            'duration': duration,
            'error': state.get('errors', {}).get(stage_name)
        }
        stages_info.append(stage_info)
    
    data['stages'] = stages_info
    data['total_stages'] = total_stages
    data['completed_stages'] = completed_stages
    
    # QC 结果
    qc_outputs = state.get('stage_outputs', {}).get('qc', {})
    if qc_outputs:
        qc_metrics = qc_outputs.get('metrics', {})
        data['qc_results'] = {
            'score': qc_metrics.get('qc_score', 'N/A'),
            'total_reads': qc_metrics.get('total_reads', 'N/A'),
            'avg_quality': qc_metrics.get('avg_quality', 'N/A'),
            'total_bases': _format_number(qc_metrics.get('total_bases', 0))
        }
        
        # 生成 QC 图表
        data['qc_chart'] = plot_quality_distribution(qc_metrics)
        
        # AI 摘要
        ai_analysis = _load_ai_analysis(state.get('workdir'), 'qc')
        if ai_analysis:
            data['qc_ai_summary'] = ai_analysis.get('quality_assessment', {}).get('summary', '')
    
    # Assembly 结果
    assembly_outputs = state.get('stage_outputs', {}).get('assembly', {})
    if assembly_outputs:
        assembly_metrics = assembly_outputs.get('metrics', {})
        data['assembly_results'] = {
            'n50': _format_number(assembly_metrics.get('n50', 0)),
            'total_length': _format_number(assembly_metrics.get('total_length', 0)),
            'num_contigs': assembly_metrics.get('num_contigs', 0),
            'quality_score': assembly_metrics.get('quality_score', 'N/A')
        }
        
        # 生成 Assembly 图表
        data['assembly_chart'] = plot_assembly_stats(assembly_metrics)
        
        # AI 摘要
        ai_analysis = _load_ai_analysis(state.get('workdir'), 'assembly')
        if ai_analysis:
            data['assembly_ai_summary'] = ai_analysis.get('assembly_quality', {}).get('summary', '')
    
    # Polishing 结果
    polish_outputs = state.get('stage_outputs', {}).get('polish', {})
    if polish_outputs:
        polish_metrics = polish_outputs.get('metrics', {})
        improvement = polish_metrics.get('improvement', {})
        
        if improvement.get('status') == 'calculated':
            data['polish_results'] = {
                'tool': polish_metrics.get('tool', 'unknown'),
                'iterations': polish_metrics.get('iterations', 1),
                'n50_change_pct': f"{improvement.get('n50_change_pct', 0):.2f}",
                'length_change': improvement.get('length_change', 0),
                'length_change_pct': f"{improvement.get('length_change_pct', 0):.2f}",
                'original': improvement.get('original', {}),
                'polished': improvement.get('polished', {}),
                'n50_change': improvement.get('n50_change', 0)
            }
            
            # 生成对比图表
            data['polish_chart'] = plot_polish_comparison(improvement)
    
    # Annotation 结果
    annotation_outputs = state.get('stage_outputs', {}).get('annotation', {})
    if annotation_outputs:
        annotation_metrics = annotation_outputs.get('metrics', {})
        data['annotation_results'] = {
            'gene_count': annotation_metrics.get('gene_count', 0),
            'trna_count': annotation_metrics.get('trna_count', 0),
            'rrna_count': annotation_metrics.get('rrna_count', 0),
            'completeness': annotation_metrics.get('completeness', 0) * 100
        }
        
        # 生成 Annotation 图表
        data['annotation_chart'] = plot_annotation_completeness(annotation_metrics)
        
        # AI 摘要
        ai_analysis = _load_ai_analysis(state.get('workdir'), 'annotation')
        if ai_analysis:
            data['annotation_ai_summary'] = ai_analysis.get('annotation_quality', {}).get('summary', '')
    
    # AI 建议
    recommendations = []
    for stage in ['qc', 'assembly', 'annotation']:
        ai_analysis = _load_ai_analysis(state.get('workdir'), stage)
        if ai_analysis and 'recommendations' in ai_analysis:
            recs = ai_analysis['recommendations']
            if isinstance(recs, list):
                recommendations.extend(recs[:3])  # 每个阶段最多 3 条
    
    data['recommendations'] = recommendations[:10]  # 总共最多 10 条
    
    # 输出文件列表
    output_files = []
    workdir = Path(state.get('workdir', '.'))
    
    for stage_name, stage_outputs in state.get('stage_outputs', {}).items():
        files = stage_outputs.get('files', {})
        for file_type, file_path in files.items():
            if file_path and Path(file_path).exists():
                file_size = Path(file_path).stat().st_size
                output_files.append({
                    'type': f"{stage_name.capitalize()} - {file_type}",
                    'path': str(Path(file_path).relative_to(workdir.parent)),
                    'size': _format_size(file_size)
                })
    
    data['output_files'] = output_files
    
    return data


def _load_ai_analysis(workdir: str, stage: str) -> Optional[Dict]:
    """加载 AI 分析结果"""
    try:
        ai_file = Path(workdir) / f"0{['qc', 'assembly', 'annotation'].index(stage) + 1}_{stage}" / f"{stage}_ai_analysis.json"
        if ai_file.exists():
            with open(ai_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.debug(f"Failed to load AI analysis for {stage}: {e}")
    return None


def _format_duration(seconds: float) -> str:
    """格式化时长"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def _format_number(num: int) -> str:
    """格式化数字（添加千位分隔符）"""
    return f"{num:,}"


def _format_size(bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024
    return f"{bytes:.1f} TB"


def _get_fallback_template() -> str:
    """获取回退模板（简化版）"""
    return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ pipeline_id }} - Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #667eea; }
        .section { margin: 20px 0; padding: 15px; background: #f5f5f5; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>Pipeline Report: {{ pipeline_id }}</h1>
    <div class="section">
        <h2>Summary</h2>
        <p>Status: {{ pipeline_status }}</p>
        <p>Time: {{ timestamp }}</p>
        <p>Duration: {{ total_time }}</p>
    </div>
    <div class="section">
        <h2>Stages</h2>
        <ul>
        {% for stage in stages %}
            <li>{{ stage.name }}: {{ stage.status }} ({{ stage.duration }})</li>
        {% endfor %}
        </ul>
    </div>
</body>
</html>
    """


def _generate_error_report(state: Dict, output_path: Path, error: str) -> Path:
    """生成错误报告"""
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Error Report</title>
</head>
<body>
    <h1>Report Generation Error</h1>
    <p>Failed to generate full report: {error}</p>
    <p>Pipeline ID: {state.get('pipeline_id', 'unknown')}</p>
    <p>Please check logs for details.</p>
</body>
</html>
    """
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return output_path
