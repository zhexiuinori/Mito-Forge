"""
Quality Control 命令

数据质量控制分析
"""

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table

from ...core.agents.qc_agent import QCAgent
from ...utils.config import Config
from ...utils.exceptions import MitoForgeError

console = Console()

@click.command()
@click.argument('input_files', nargs=-1, required=True, type=click.Path(exists=True))
@click.option('-o', '--output-dir', default='./qc_results',
              help='输出目录 (默认: ./qc_results)')
@click.option('-q', '--quality-threshold', default=20, type=int,
              help='质量阈值 (默认: 20)')
@click.option('-j', '--threads', default=4, type=int,
              help='线程数 (默认: 4)')
@click.option('--adapter-removal', is_flag=True,
              help='执行接头序列去除')
@click.option('--trim-quality', default=20, type=int,
              help='修剪质量阈值 (默认: 20)')
@click.option('--min-length', default=50, type=int,
              help='最小序列长度 (默认: 50)')
@click.option('--report-only', is_flag=True,
              help='仅生成质控报告，不进行数据处理')
@click.pass_context
def qc(ctx, input_files, output_dir, quality_threshold, threads, 
       adapter_removal, trim_quality, min_length, report_only):
    """
    执行质量控制分析
    
    INPUT_FILES: 输入的FASTQ文件路径
    
    示例:
        mito-forge qc sample_R1.fastq sample_R2.fastq
        mito-forge qc *.fastq --adapter-removal --threads 8
    """
    verbose = ctx.obj.get('verbose', False)
    quiet = ctx.obj.get('quiet', False)
    
    try:
        if not quiet:
            console.print("\n🔍 [bold blue]质量控制分析[/bold blue]")
            console.print(f"📁 输入文件: {', '.join(input_files)}")
            console.print(f"📂 输出目录: {output_dir}")
            console.print(f"📊 质量阈值: {quality_threshold}")
            console.print(f"⚡ 线程数: {threads}\n")
        
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 配置参数
        config = Config()
        config.update({
            'quality_threshold': quality_threshold,
            'threads': threads,
            'adapter_removal': adapter_removal,
            'trim_quality': trim_quality,
            'min_length': min_length,
            'report_only': report_only,
            'verbose': verbose
        })
        
        # 初始化QC智能体
        qc_agent = QCAgent(config)
        
        # 执行质控分析
        with console.status("[bold green]执行质控分析...") if not quiet else console:
            results = qc_agent.analyze(
                input_files=list(input_files),
                output_dir=str(output_path)
            )
        
        # 显示结果
        if not quiet:
            console.print("✅ [bold green]质控分析完成！[/bold green]\n")
            
            # 创建结果表格
            table = Table(title="质控分析结果", show_header=True, header_style="bold magenta")
            table.add_column("文件", style="cyan")
            table.add_column("原始读长数", justify="right")
            table.add_column("过滤后读长数", justify="right")
            table.add_column("平均质量", justify="right")
            table.add_column("状态", justify="center")
            
            for file_result in results.get('files', []):
                status = "✅ 通过" if file_result['quality_passed'] else "❌ 未通过"
                table.add_row(
                    file_result['filename'],
                    str(file_result['raw_reads']),
                    str(file_result['filtered_reads']),
                    f"{file_result['avg_quality']:.1f}",
                    status
                )
            
            console.print(table)
            console.print(f"\n📄 详细报告: [link]{output_path}/qc_report.html[/link]")
        
        return 0
        
    except MitoForgeError as e:
        console.print(f"\n❌ [bold red]错误:[/bold red] {e}")
        if verbose:
            console.print_exception()
        return 1
    except Exception as e:
        console.print(f"\n💥 [bold red]未预期的错误:[/bold red] {e}")
        if verbose:
            console.print_exception()
        return 1