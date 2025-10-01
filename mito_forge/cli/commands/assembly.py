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

import os
def _t(key):
    lang = os.getenv("MITO_LANG", "zh")
    texts = {
        "zh": {
            "asm_title": "基因组组装分析",
            "input_files": "输入文件",
            "output_dir": "输出目录",
            "assembler": "组装器",
            "threads": "线程数",
            "memory": "内存限制",
            "asm_running": "执行基因组组装...",
            "asm_done": "基因组组装完成！",
            "asm_stats": "组装统计",
            "asm_file": "组装文件"
        },
        "en": {
            "asm_title": "Genome Assembly Analysis",
            "input_files": "Input files",
            "output_dir": "Output directory",
            "assembler": "Assembler",
            "threads": "Threads",
            "memory": "Memory limit",
            "asm_running": "Running genome assembly...",
            "asm_done": "Genome assembly completed!",
            "asm_stats": "Assembly stats",
            "asm_file": "Assembly file"
        }
    }
    return texts.get(lang, texts["zh"]).get(key, key)

from ...utils.i18n import t as _t

def _help(key):
    import sys, os as _os
    lang = "en" if ("--lang" in sys.argv and "en" in sys.argv) else _os.getenv("MITO_LANG", "zh")
    from ...utils.i18n import t as _tt
    return _tt(key, lang)

@click.command(help=_help("asm.help.desc"))
@click.argument('input_files', nargs=-1, required=True, type=click.Path(exists=True))
@click.option('-o', '--output-dir', default='./assembly_results',
              help=_help('asm.opt.output_dir'))
@click.option('-a', '--assembler', 
              type=click.Choice(['spades', 'unicycler', 'flye']), 
              default='spades',
              help=_help('asm.opt.assembler'))
@click.option('-j', '--threads', default=4, type=int,
              help=_help('asm.opt.threads'))
@click.option('-m', '--memory', default='8G',
              help=_help('asm.opt.memory'))
@click.option('--k-values', default='21,33,55,77',
              help=_help('asm.opt.k_values'))
@click.option('--careful-mode', is_flag=True,
              help=_help('asm.opt.careful_mode'))
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
        # Simulation hook
        sim = os.getenv("MITO_SIM", "")
        sim_map = dict(kv.split("=", 1) for kv in sim.split(",") if "=" in kv) if sim else {}
        scenario = sim_map.get("assembly")
        if scenario:
            # prepare output dir
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            lang = os.getenv("MITO_LANG", "zh")
            def msg(zh, en): return zh if lang == "zh" else en

            if scenario == "ok":
                if not quiet:
                    console.print(f"\n🧬 [bold blue]{_t('asm_title')}[/bold blue]")
                    console.print(f"📁 {_t('input_files')}: {', '.join(input_files)}")
                    console.print(f"📂 {_t('output_dir')}: {output_dir}")
                    console.print(f"🔧 {_t('assembler')}: {assembler}")
                    console.print(f"⚡ {_t('threads')}: {threads}")
                    console.print(f"💾 {_t('memory')}: {memory}\n")
                    console.print(f"✅ [bold green]{_t('asm_done')}[/bold green]\n")
                    console.print(f"📊 {_t('asm_stats')}:")
                    console.print(f"  • Contigs数量: 52")
                    console.print(f"  • 总长度: 16543 bp")
                    console.print(f"  • N50: 10321 bp")
                    console.print(f"  • 最长contig: 15230 bp")
                    console.print(f"\n📄 {_t('asm_file')}: [link]{output_path}/contigs.fasta[/link]")
                return 0
            elif scenario == "assembler_not_found":
                console.print(f"\n❌ [bold red]{msg('组装器不可用或未安装','Assembler not found or unavailable')}[/bold red]")
                console.print(msg("尝试切换为 spades/unicycler/flye 或运行 doctor --fix-issues",
                                  "Try spades/unicycler/flye or run doctor --fix-issues"))
                raise SystemExit(1)
            elif scenario == "memory_exceeded":
                console.print(f"\n💥 [bold red]{msg('内存不足','Memory exceeded')}[/bold red]")
                console.print(msg("降低线程/调整 K-mer 或增大内存后重试",
                                  "Reduce threads/tune K-mer or increase memory"))
                raise SystemExit(1)
            elif scenario == "timeout":
                console.print(f"\n⏱️ [bold red]{msg('执行超时','Execution timeout')}[/bold red]")
                console.print(msg("可减少线程/缩小数据量后重试",
                                  "Try fewer threads or smaller input chunks"))
                raise SystemExit(1)
        if not quiet:
            console.print(f"\n🧬 [bold blue]{_t('asm_title')}[/bold blue]")
            console.print(f"📁 {_t('input_files')}: {', '.join(input_files)}")
            console.print(f"📂 {_t('output_dir')}: {output_dir}")
            console.print(f"🔧 {_t('assembler')}: {assembler}")
            console.print(f"⚡ {_t('threads')}: {threads}")
            console.print(f"💾 {_t('memory')}: {memory}\n")
        
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
        with console.status(f"[bold green]{_t('asm_running')}") if not quiet else console:
            results = assembly_agent.assemble(
                input_files=list(input_files),
                output_dir=str(output_path)
            )
        
        # 显示结果
        if not quiet:
            console.print(f"✅ [bold green]{_t('asm_done')}[/bold green]\n")
            console.print(f"📊 {_t('asm_stats')}:")
            console.print(f"  • Contigs数量: {results.get('num_contigs', 'N/A')}")
            console.print(f"  • 总长度: {results.get('total_length', 'N/A')} bp")
            console.print(f"  • N50: {results.get('n50', 'N/A')} bp")
            console.print(f"  • 最长contig: {results.get('longest_contig', 'N/A')} bp")
            console.print(f"\n📄 {_t('asm_file')}: [link]{output_path}/contigs.fasta[/link]")
        
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