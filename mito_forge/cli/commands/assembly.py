"""
Assembly 命令

基因组组装分析
"""

import click
from pathlib import Path
from rich.console import Console

from ...core.agents.assembly_agent import AssemblyAgent
from ...utils.config import Config
from ...utils.exceptions import MitoForgeError

console = Console()

@click.command()
@click.argument('input_files', nargs=-1, required=True, type=click.Path(exists=True))
@click.option('-o', '--output-dir', default='./assembly_results',
              help='输出目录 (默认: ./assembly_results)')
@click.option('-a', '--assembler', 
              type=click.Choice(['spades', 'unicycler', 'flye']), 
              default='spades',
              help='组装器选择 (默认: spades)')
@click.option('-j', '--threads', default=4, type=int,
              help='线程数 (默认: 4)')
@click.option('-m', '--memory', default='8G',
              help='内存限制 (默认: 8G)')
@click.option('--k-values', default='21,33,55,77',
              help='K-mer值 (默认: 21,33,55,77)')
@click.option('--careful-mode', is_flag=True,
              help='启用careful模式（更慢但更准确）')
@click.pass_context
def assembly(ctx, input_files, output_dir, assembler, threads, memory, k_values, careful_mode):
    """
    执行基因组组装分析
    
    INPUT_FILES: 输入的FASTQ文件路径
    
    示例:
        mito-forge assembly sample_R1.fastq sample_R2.fastq
        mito-forge assembly *.fastq --assembler unicycler --threads 8
    """
    verbose = ctx.obj.get('verbose', False)
    quiet = ctx.obj.get('quiet', False)
    
    try:
        if not quiet:
            console.print("\n🧬 [bold blue]基因组组装分析[/bold blue]")
            console.print(f"📁 输入文件: {', '.join(input_files)}")
            console.print(f"📂 输出目录: {output_dir}")
            console.print(f"🔧 组装器: {assembler}")
            console.print(f"⚡ 线程数: {threads}")
            console.print(f"💾 内存限制: {memory}\n")
        
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 配置参数
        config = Config()
        config.update({
            'assembler': assembler,
            'threads': threads,
            'memory': memory,
            'k_values': [int(k) for k in k_values.split(',')],
            'careful_mode': careful_mode,
            'verbose': verbose
        })
        
        # 初始化组装智能体
        assembly_agent = AssemblyAgent(config)
        
        # 执行组装
        with console.status("[bold green]执行基因组组装...") if not quiet else console:
            results = assembly_agent.assemble(
                input_files=list(input_files),
                output_dir=str(output_path)
            )
        
        # 显示结果
        if not quiet:
            console.print("✅ [bold green]基因组组装完成！[/bold green]\n")
            console.print(f"📊 组装统计:")
            console.print(f"  • Contigs数量: {results.get('num_contigs', 'N/A')}")
            console.print(f"  • 总长度: {results.get('total_length', 'N/A')} bp")
            console.print(f"  • N50: {results.get('n50', 'N/A')} bp")
            console.print(f"  • 最长contig: {results.get('longest_contig', 'N/A')} bp")
            console.print(f"\n📄 组装文件: [link]{output_path}/contigs.fasta[/link]")
        
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