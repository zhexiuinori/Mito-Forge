"""
Pipeline 命令

完整的线粒体基因组分析流水线
"""

import click
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from ...core.pipeline.manager import PipelineManager
from ...utils.config import Config
from ...utils.exceptions import MitoForgeError

console = Console()

@click.command()
@click.argument('input_files', nargs=-1, required=True, type=click.Path(exists=True))
@click.option('-o', '--output-dir', default='./mito_forge_results', 
              help='输出目录 (默认: ./mito_forge_results)')
@click.option('-q', '--quality-threshold', default=20, type=int,
              help='质量阈值 (默认: 20)')
@click.option('-a', '--assembler', 
              type=click.Choice(['spades', 'unicycler', 'flye']), 
              default='spades',
              help='组装器选择 (默认: spades)')
@click.option('-t', '--annotation-tool',
              type=click.Choice(['mitos', 'geseq', 'prokka']),
              default='mitos', 
              help='注释工具选择 (默认: mitos)')
@click.option('-j', '--threads', default=4, type=int,
              help='线程数 (默认: 4)')
@click.option('-m', '--memory', default='8G',
              help='内存限制 (默认: 8G)')
@click.option('--skip-qc', is_flag=True, help='跳过质量控制步骤')
@click.option('--skip-assembly', is_flag=True, help='跳过组装步骤')
@click.option('--skip-annotation', is_flag=True, help='跳过注释步骤')
@click.option('--config-file', type=click.Path(exists=True),
              help='自定义配置文件路径')
@click.pass_context
def pipeline(ctx, input_files, output_dir, quality_threshold, assembler, 
            annotation_tool, threads, memory, skip_qc, skip_assembly, 
            skip_annotation, config_file):
    """
    运行完整的线粒体基因组分析流水线
    
    INPUT_FILES: 输入的FASTQ文件路径（支持多个文件）
    
    示例:
        mito-forge pipeline sample_R1.fastq sample_R2.fastq
        mito-forge pipeline *.fastq -o results/ --threads 8
    """
    verbose = ctx.obj.get('verbose', False)
    quiet = ctx.obj.get('quiet', False)
    
    try:
        # 显示分析信息
        if not quiet:
            console.print("\n🧬 [bold blue]Mito-Forge 流水线分析[/bold blue]")
            console.print(f"📁 输入文件: {', '.join(input_files)}")
            console.print(f"📂 输出目录: {output_dir}")
            console.print(f"🔧 组装器: {assembler}")
            console.print(f"📝 注释工具: {annotation_tool}")
            console.print(f"⚡ 线程数: {threads}")
            console.print(f"💾 内存限制: {memory}\n")
        
        # 加载配置
        config = Config(config_file) if config_file else Config()
        
        # 更新配置参数
        config.update({
            'quality_threshold': quality_threshold,
            'assembler': assembler,
            'annotation_tool': annotation_tool,
            'threads': threads,
            'memory': memory,
            'skip_qc': skip_qc,
            'skip_assembly': skip_assembly,
            'skip_annotation': skip_annotation,
            'verbose': verbose
        })
        
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 初始化流水线管理器
        pipeline_manager = PipelineManager(config)
        
        # 运行流水线
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
            disable=quiet
        ) as progress:
            
            # 添加总体进度任务
            total_task = progress.add_task("🚀 执行流水线分析", total=100)
            
            # 运行分析
            results = pipeline_manager.run_pipeline(
                input_files=list(input_files),
                output_dir=str(output_path),
                progress_callback=lambda step, percent: progress.update(total_task, completed=percent)
            )
        
        # 显示结果
        if not quiet:
            console.print("\n✅ [bold green]流水线分析完成！[/bold green]")
            console.print(f"📊 结果保存在: [bold]{output_path}[/bold]")
            
            if results.get('summary'):
                console.print("\n📋 [bold]分析摘要:[/bold]")
                for key, value in results['summary'].items():
                    console.print(f"  • {key}: {value}")
            
            console.print(f"\n📄 详细报告: [link]{output_path}/pipeline_report.html[/link]")
        
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