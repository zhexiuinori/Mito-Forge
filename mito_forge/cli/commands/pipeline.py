"""
基于 LangGraph 的流水线命令
"""
import click
import json
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from ...graph.build import run_pipeline_sync, save_checkpoint, resume_pipeline
from ...graph.state import init_pipeline_state
from ...utils.logging import setup_logging

console = Console()

from ...utils.i18n import tl as _t
import sys
def _help(key: str) -> str:
    lang = None
    try:
        if '--lang' in sys.argv:
            args = sys.argv
            for i, a in enumerate(args):
                if a == '--lang' and i + 1 < len(args):
                    lang = args[i + 1]
                    break
        if lang is None:
            lang = os.getenv('MITO_LANG', 'zh')
    except Exception:
        lang = os.getenv('MITO_LANG', 'zh')
    # 复用 t(lang,key) 语义：tl(lang, key)
    return _t(lang, key)

@click.command()
@click.option("--reads", type=click.Path(exists=True), required=True, help=_help("pl_opt_reads"))
@click.option("--output", "-o", type=click.Path(), default="results", help=_help("pl_opt_output"))
@click.option("--threads", "-t", type=int, default=8, help=_help("pl_opt_threads"))
@click.option("--kingdom", type=click.Choice(["animal", "plant"]), default="animal", help=_help("pl_opt_kingdom"))
@click.option("--resume", type=click.Path(), help=_help("pl_opt_resume"))
@click.option("--checkpoint", type=click.Path(), help=_help("pl_opt_checkpoint"))
@click.option("--config-file", type=click.Path(exists=True), help=_help("pl_opt_config_file"))
@click.option("--verbose", "-v", is_flag=True, help=_help("pl_opt_verbose"))
@click.option("--interactive", is_flag=True, help=_help("pl_opt_interactive"))
@click.option("--lang", type=click.Choice(["zh","en"]), default="zh", help=_help("pl_opt_lang"))
def pipeline(reads, output, threads, kingdom, resume, checkpoint, config_file, verbose, interactive, lang):
    """
    运行完整的线粒体基因组组装流水线 / Run the complete mitochondrial genome assembly pipeline

    使用 LangGraph 状态机协调多个智能体：
    Coordinate multiple agents with LangGraph state machine:
      - Supervisor: 分析并制定计划 / Analyze and plan
      - QC Agent: 质量控制 / Quality Control
      - Assembly Agent: 组装 / Assembly
      - Annotation Agent: 注释 / Annotation
      - Report Agent: 生成报告 / Reporting
    """
    
    os.environ["MITO_LANG"] = lang
    # 设置日志
    log_level = "DEBUG" if verbose else "INFO"
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    setup_logging(
        level=log_level,
        log_file=str(output_dir / "logs" / "pipeline.log")
    )
    
    console.print(f"[bold blue]{_t(lang, 'header')}[/bold blue]")
    console.print(f"{_t(lang, 'input_file')}: {reads}")
    console.print(f"{_t(lang, 'output_dir')}: {output}")
    console.print(f"{_t(lang, 'kingdom')}: {kingdom}")
    console.print()
    
    try:
        # 从检查点恢复
        if resume:
            console.print(f"[yellow]{_t(lang, 'resume_from')}: {resume}[/yellow]")
            final_state = resume_pipeline(resume)
        else:
            # 准备输入和配置
            inputs = {
                "reads": str(reads),
                "kingdom": kingdom  # 确保kingdom参数传递到inputs中
            }
            
            config = {
                "threads": threads,
                "kingdom": kingdom,  # 同时也放在config中作为备份
                "output_dir": str(output_dir)
            }
            
            # 加载配置文件
            if config_file:
                with open(config_file) as f:
                    file_config = json.load(f)
                    config.update(file_config)
            
            # 运行流水线 - 使用简单的状态显示避免与日志混合
            console.print(f"🔄 [bold blue]{_t(lang, 'start')}[/bold blue]")
            
            final_state = run_pipeline_sync(
                inputs=inputs,
                config=config,
                workdir=str(output_dir / "work"),
                pipeline_id=None
            )
            
            console.print(f"✅ [bold green]{_t(lang, 'done')}[/bold green]")
        
        # 保存检查点
        if checkpoint:
            save_checkpoint(final_state, checkpoint)
            console.print(f"[green]{'检查点已保存' if lang!='en' else 'Checkpoint saved'}: {checkpoint}[/green]")
        
        # 显示结果摘要
        show_pipeline_summary(final_state, output_dir, lang)
        
        if final_state["done"]:
            console.print("[bold green]✅ Pipeline succeeded![/bold green]" if lang=="en" else "[bold green]✅ 流水线执行成功！[/bold green]")
        else:
            console.print("[bold red]❌ Pipeline failed[/bold red]" if lang=="en" else "[bold red]❌ 流水线执行失败[/bold red]")
            for error in final_state["errors"]:
                console.print(f"[red]{('错误' if lang!='en' else 'Error')}: {error}[/red]")
            # 交互式错误处理占位实现
            if interactive:
                console.print("[bold yellow]" + ("主管建议：" if lang!="en" else "Supervisor suggestions:") + "[/bold yellow]")
                console.print("  " + ("1) 重试当前阶段（使用默认修复参数）" if lang!="en" else "1) Retry current stage (with default fix parameters)"))
                console.print("  " + ("2) 跳过当前阶段继续执行" if lang!="en" else "2) Skip current stage and continue"))
                console.print("  " + ("3) 终止并返回诊断建议" if lang!="en" else "3) Terminate and return diagnostic suggestions"))
                try:
                    choice = int(console.input(("请选择 [1/2/3]: " if lang!="en" else "Choose [1/2/3]: ")).strip() or "3")
                except Exception:
                    choice = 3
                if choice == 1:
                    console.print("[cyan]" + ("重试功能尚未集成到 LangGraph 流程，此为占位提示。" if lang!="en" else "Retry is not integrated into the LangGraph flow yet. Placeholder message.") + "[/cyan]")
                elif choice == 2:
                    console.print("[cyan]" + ("跳过阶段继续的策略需在编排器中启用，此为占位提示。" if lang!="en" else "Skipping strategy needs to be enabled in the orchestrator. Placeholder message.") + "[/cyan]")
                else:
                    console.print("[cyan]" + ("已终止。建议：检查输入文件与外部工具环境（使用 doctor 命令）。" if lang!="en" else "Terminated. Suggestion: Check input files and external tool environment (use the doctor command).") + "[/cyan]")
            return 1
            
    except Exception as e:
        console.print(("[bold red]流水线执行出错: " if lang!="en" else "[bold red]Pipeline error: ") + f"{e}[/bold red]")
        return 1
    
    return 0

def show_pipeline_summary(state, output_dir, lang):
    """显示流水线执行摘要"""
    
    # 使用简单的文本格式显示，避免表格宽度问题
    console.print(f"\n[bold blue]{_t(lang, 'summary_title')}[/bold blue]")
    console.print("=" * 50)
    
    console.print(f"[cyan]{_t(lang, 'pipeline_id')}:[/cyan] {state['pipeline_id']}")
    console.print(f"[cyan]{_t(lang, 'status')}:[/cyan] {_t(lang, 'status_done') if state['done'] else _t(lang, 'status_running')}")
    console.print(f"[cyan]{_t(lang, 'current_stage')}:[/cyan] {state['current_stage']}")
    console.print(f"[cyan]{_t(lang, 'completed_stages')}:[/cyan] {', '.join(state['completed_stages'])}")
    
    if state.get("end_time"):
        duration = state["end_time"] - state["start_time"]
        console.print(f"[cyan]{_t(lang, 'duration')}:[/cyan] {duration:.2f} {_t(lang, 'seconds')}")
    
    # 各阶段结果
    if state["stage_outputs"]:
        console.print(f"\n[bold blue]{_t(lang, 'stage_results')}[/bold blue]")
        console.print("=" * 50)
        
        for stage, outputs in state["stage_outputs"].items():
            metrics = outputs.get("metrics", {})
            files = outputs.get("files", {})
            
            console.print(f"\n[bold yellow]{stage.upper()}:[/bold yellow]")
            
            # 显示关键指标
            if metrics:
                console.print(f"  [cyan]{_t(lang, 'metrics')}:[/cyan]")
                for k, v in list(metrics.items())[:3]:
                    if isinstance(v, float):
                        console.print(f"    • {k}: {v:.3f}")
                    else:
                        console.print(f"    • {k}: {v}")
                if len(metrics) > 3:
                    console.print(f"    • ... {len(metrics)-3} {_t(lang, 'more_metrics')}")
            
            # 显示输出文件
            if files:
                console.print(f"  [green]{_t(lang, 'files')}:[/green]")
                for k, v in list(files.items())[:3]:
                    file_name = Path(v).name
                    console.print(f"    • {k}: {file_name}")
                if len(files) > 3:
                    console.print(f"    • ... {len(files)-3} {_t(lang, 'more_files')}")
    
    console.print()
    
    # 错误和警告
    if state["errors"]:
        console.print(f"[bold red]{_t(lang, 'errors')}:[/bold red]")
        for error in state["errors"]:
            console.print(f"  [red]• {error}[/red]")
        console.print()
    
    if state["warnings"]:
        console.print(f"[bold yellow]{_t(lang, 'warnings')}:[/bold yellow]")
        for warning in state["warnings"]:
            console.print(f"  [yellow]• {warning}[/yellow]")
        console.print()
    
    # 输出文件位置
    console.print(f"[bold]{_t(lang, 'main_outputs')}:[/bold]")
    
    # QC 结果
    if "qc" in state["stage_outputs"]:
        qc_files = state["stage_outputs"]["qc"]["files"]
        qc_report_path = qc_files.get('qc_report', 'N/A')
        if qc_report_path != 'N/A':
            qc_report_path = str(Path(qc_report_path)).replace('\\', '/')
        console.print(f"  {_t(lang, 'qc_report')}: {qc_report_path}")
    
    # 组装结果
    if "assembly" in state["stage_outputs"]:
        assembly_files = state["stage_outputs"]["assembly"]["files"]
        mito_path = assembly_files.get('mito_candidates', 'N/A')
        stats_path = assembly_files.get('assembly_stats', 'N/A')
        if mito_path != 'N/A':
            mito_path = str(Path(mito_path)).replace('\\', '/')
        if stats_path != 'N/A':
            stats_path = str(Path(stats_path)).replace('\\', '/')
        console.print(f"  {_t(lang, 'mito_seq')}: {mito_path}")
        console.print(f"  {_t(lang, 'assembly_stats')}: {stats_path}")
    
    # 注释结果
    if "annotation" in state["stage_outputs"]:
        annotation_files = state["stage_outputs"]["annotation"]["files"]
        gff_path = annotation_files.get('gff', 'N/A')
        table_path = annotation_files.get('annotation_table', 'N/A')
        if gff_path != 'N/A':
            gff_path = str(Path(gff_path)).replace('\\', '/')
        if table_path != 'N/A':
            table_path = str(Path(table_path)).replace('\\', '/')
        console.print(f"  {_t(lang, 'gff')}: {gff_path}")
        console.print(f"  {_t(lang, 'table')}: {table_path}")
    
    # 最终报告
    if "report" in state["stage_outputs"]:
        report_path = str(Path(output_dir) / "report" / "pipeline_report.html").replace('\\', '/')
        console.print(f"  [bold green]{_t(lang, 'final_report')}: {report_path}[/bold green]")

@click.command()
@click.option("--checkpoint", type=click.Path(exists=True), required=True, help=_help("pl_opt_checkpoint"))
def status(checkpoint):
    """查看流水线状态 / Show pipeline status"""
    try:
        from ...graph.build import load_checkpoint
        
        state = load_checkpoint(checkpoint)
        show_pipeline_summary(state, Path("."), os.getenv("MITO_LANG","zh"))
        
    except Exception as e:
        lang = os.getenv("MITO_LANG","zh")
        console.print(("[red]无法加载检查点: " if lang!="en" else "[red]Failed to load checkpoint: ") + f"{e}[/red]")
        return 1

if __name__ == "__main__":
    pipeline()