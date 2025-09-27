"""
Annotate 命令

基因注释分析
"""

import click
from pathlib import Path
from rich.console import Console

from ...core.agents.annotation_agent import AnnotationAgent
from ...utils.config import Config
from ...utils.exceptions import MitoForgeError

console = Console()

@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('-o', '--output-dir', default='./annotation_results',
              help='输出目录 (默认: ./annotation_results)')
@click.option('-t', '--annotation-tool',
              type=click.Choice(['mitos', 'geseq', 'prokka']),
              default='mitos',
              help='注释工具选择 (默认: mitos)')
@click.option('-j', '--threads', default=4, type=int,
              help='线程数 (默认: 4)')
@click.option('--genetic-code', default=2, type=int,
              help='遗传密码表 (默认: 2 - 脊椎动物线粒体)')
@click.option('--reference-db', default='mitochondria',
              help='参考数据库 (默认: mitochondria)')
@click.pass_context
def annotate(ctx, input_file, output_dir, annotation_tool, threads, genetic_code, reference_db):
    """
    执行基因注释分析
    
    INPUT_FILE: 输入的FASTA文件路径
    
    示例:
        mito-forge annotate contigs.fasta
        mito-forge annotate genome.fasta --annotation-tool mitos --threads 8
    """
    verbose = ctx.obj.get('verbose', False)
    quiet = ctx.obj.get('quiet', False)
    
    try:
        if not quiet:
            console.print("\n📝 [bold blue]基因注释分析[/bold blue]")
            console.print(f"📁 输入文件: {input_file}")
            console.print(f"📂 输出目录: {output_dir}")
            console.print(f"🔧 注释工具: {annotation_tool}")
            console.print(f"⚡ 线程数: {threads}")
            console.print(f"🧬 遗传密码表: {genetic_code}\n")
        
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 配置参数
        config = Config()
        config.update({
            'annotation_tool': annotation_tool,
            'threads': threads,
            'genetic_code': genetic_code,
            'reference_db': reference_db,
            'verbose': verbose
        })
        
        # 初始化注释智能体
        annotation_agent = AnnotationAgent(config)
        
        # 执行注释
        with console.status("[bold green]执行基因注释...") if not quiet else console:
            results = annotation_agent.annotate(
                input_file=input_file,
                output_dir=str(output_path)
            )
        
        # 显示结果
        if not quiet:
            console.print("✅ [bold green]基因注释完成！[/bold green]\n")
            console.print(f"📊 注释统计:")
            console.print(f"  • 蛋白编码基因: {results.get('protein_genes', 'N/A')}")
            console.print(f"  • tRNA基因: {results.get('trna_genes', 'N/A')}")
            console.print(f"  • rRNA基因: {results.get('rrna_genes', 'N/A')}")
            console.print(f"  • 总基因数: {results.get('total_genes', 'N/A')}")
            console.print(f"\n📄 注释文件: [link]{output_path}/annotation.gff[/link]")
            console.print(f"📄 GenBank文件: [link]{output_path}/annotation.gb[/link]")
        
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