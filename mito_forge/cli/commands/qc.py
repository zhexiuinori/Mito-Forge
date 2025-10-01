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

import os
def _t(key):
    lang = os.getenv("MITO_LANG", "zh")
    texts = {
        "zh": {
            "qc_title": "质量控制分析",
            "input_files": "输入文件",
            "output_dir": "输出目录",
            "quality_threshold": "质量阈值",
            "threads": "线程数",
            "qc_running": "执行质控分析...",
            "qc_done": "质控分析完成！",
            "qc_results_title": "质控分析结果",
            "col_file": "文件",
            "col_raw_reads": "原始读长数",
            "col_filtered_reads": "过滤后读长数",
            "col_avg_quality": "平均质量",
            "col_status": "状态",
            "pass": "✅ 通过",
            "fail": "❌ 未通过",
            "detail_report": "详细报告"
        },
        "en": {
            "qc_title": "Quality Control Analysis",
            "input_files": "Input files",
            "output_dir": "Output directory",
            "quality_threshold": "Quality threshold",
            "threads": "Threads",
            "qc_running": "Running QC analysis...",
            "qc_done": "QC analysis completed!",
            "qc_results_title": "QC Results",
            "col_file": "File",
            "col_raw_reads": "Raw reads",
            "col_filtered_reads": "Filtered reads",
            "col_avg_quality": "Avg quality",
            "col_status": "Status",
            "pass": "✅ Passed",
            "fail": "❌ Failed",
            "detail_report": "Detailed report"
        }
    }
    return texts.get(lang, texts["zh"]).get(key, key)

from ...utils.i18n import t as _t

def _help(key):
    import sys, os as _os
    lang = "en" if ("--lang" in sys.argv and "en" in sys.argv) else _os.getenv("MITO_LANG", "zh")
    from ...utils.i18n import t as _tt
    return _tt(key, lang)

@click.command(help=_help("qc.help.desc"))
@click.argument('input_files', nargs=-1, required=True, type=click.Path(exists=True))
@click.option('-o', '--output-dir', default='./qc_results',
              help=_help('qc.opt.output_dir'))
@click.option('-q', '--quality-threshold', default=20, type=int,
              help=_help('qc.opt.quality_threshold'))
@click.option('-j', '--threads', default=4, type=int,
              help=_help('qc.opt.threads'))
@click.option('--adapter-removal', is_flag=True,
              help=_help('qc.opt.adapter_removal'))
@click.option('--trim-quality', default=20, type=int,
              help=_help('qc.opt.trim_quality'))
@click.option('--min-length', default=50, type=int,
              help=_help('qc.opt.min_length'))
@click.option('--report-only', is_flag=True,
              help=_help('qc.opt.report_only'))
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
            console.print(f"\n🔍 [bold blue]{_t('qc_title')}[/bold blue]")
            console.print(f"📁 {_t('input_files')}: {', '.join(input_files)}")
            console.print(f"📂 {_t('output_dir')}: {output_dir}")
            console.print(f"📊 {_t('quality_threshold')}: {quality_threshold}")
            console.print(f"⚡ {_t('threads')}: {threads}\n")
        
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 模拟执行（Windows环境/无依赖演示用）
        sim = os.getenv("MITO_SIM", "")
        sim_map = dict(kv.split("=", 1) for kv in sim.split(",") if "=" in kv) if sim else {}
        scenario = sim_map.get("qc")
        if scenario:
            lang = os.getenv("MITO_LANG", "zh")
            def msg(zh, en): return zh if lang == "zh" else en
            if scenario == "ok":
                if not quiet:
                    console.print(f"✅ [bold green]{_t('qc_done')}[/bold green]\n")
                    table = Table(title=_t("qc_results_title"), show_header=True, header_style="bold magenta")
                    table.add_column(_t("col_file"), style="cyan", width=25)
                    table.add_column(_t("col_raw_reads"), justify="right", width=12)
                    table.add_column(_t("col_filtered_reads"), justify="right", width=14)
                    table.add_column(_t("col_avg_quality"), justify="right", width=10)
                    table.add_column(_t("col_status"), justify="center", width=10)
                    table.add_row("R1.fastq", "1,000,000", "950,000", "32.1", _t("pass"))
                    table.add_row("R2.fastq", "1,000,000", "948,000", "31.8", _t("pass"))
                    console.print(table)
                    console.print(f"📄 {_t('detail_report')}: [link]{output_path}/qc_report.html[/link]")
                return 0
            elif scenario == "tool_missing":
                console.print(f"❌ [bold red]{msg('质控工具缺失或未安装','QC tool missing or not installed')}[/bold red]")
                console.print(msg("请安装或配置所需工具（如 fastp/fastqc）后重试",
                                  "Install or configure required tools (e.g., fastp/fastqc) and retry"))
                raise SystemExit(1)
            elif scenario == "timeout":
                console.print(f"⏱️ [bold red]{msg('执行超时','Execution timeout')}[/bold red]")
                console.print(msg("可减少线程/缩小数据量后重试",
                                  "Try fewer threads or smaller input chunks"))
                raise SystemExit(1)
            elif scenario == "low_quality":
                if not quiet:
                    console.print(f"⚠️ {msg('样本整体质量偏低','Overall sample quality is low')}")
                    console.print(f"✅ [bold green]{_t('qc_done')}[/bold green]\n")
                    table = Table(title=_t("qc_results_title"), show_header=True, header_style="bold magenta")
                    table.add_column(_t("col_file"), style="cyan", width=25)
                    table.add_column(_t("col_raw_reads"), justify="right", width=12)
                    table.add_column(_t("col_filtered_reads"), justify="right", width=14)
                    table.add_column(_t("col_avg_quality"), justify="right", width=10)
                    table.add_column(_t("col_status"), justify="center", width=10)
                    table.add_row("R1.fastq", "1,000,000", "600,000", "18.5", _t("fail"))
                    table.add_row("R2.fastq", "1,000,000", "610,000", "18.9", _t("fail"))
                    console.print(table)
                    console.print(f"📄 {_t('detail_report')}: [link]{output_path}/qc_report.html[/link]")
                return 0
        
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
        with console.status(f"[bold green]{_t('qc_running')}") if not quiet else console:
            results = qc_agent.analyze(
                input_files=list(input_files),
                output_dir=str(output_path)
            )
        
        # 显示结果
        if not quiet:
            console.print(f"✅ [bold green]{_t('qc_done')}[/bold green]\n")
            
            # 创建结果表格
            table = Table(title=_t("qc_results_title"), show_header=True, header_style="bold magenta")
            table.add_column(_t("col_file"), style="cyan", width=25)
            table.add_column(_t("col_raw_reads"), justify="right", width=12)
            table.add_column(_t("col_filtered_reads"), justify="right", width=14)
            table.add_column(_t("col_avg_quality"), justify="right", width=10)
            table.add_column(_t("col_status"), justify="center", width=10)
            
            for file_result in results.get('files', []):
                status = _t("pass") if file_result['quality_passed'] else _t("fail")
                table.add_row(
                    file_result['filename'],
                    str(file_result['raw_reads']),
                    str(file_result['filtered_reads']),
                    f"{file_result['avg_quality']:.1f}",
                    status
                )
            
            console.print(table)
            console.print(f"\n📄 {_t('detail_report')}: [link]{output_path}/qc_report.html[/link]")
        
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