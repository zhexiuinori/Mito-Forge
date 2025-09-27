"""
Mito-Forge 主CLI入口

统一的命令行界面，提供所有功能的访问点
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .. import __version__
from .commands import pipeline, qc, assembly, annotate, doctor, config, agents

console = Console()

def print_banner():
    """显示Mito-Forge横幅"""
    banner = Text("🧬 Mito-Forge", style="bold blue")
    subtitle = Text("线粒体基因组学多智能体自动化框架", style="dim")
    
    panel = Panel.fit(
        f"{banner}\n{subtitle}",
        border_style="blue",
        padding=(1, 2)
    )
    console.print(panel)

@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='显示版本信息')
@click.option('-v', '--verbose', is_flag=True, help='详细输出模式')
@click.option('-q', '--quiet', is_flag=True, help='静默模式')
@click.pass_context
def main(ctx, version, verbose, quiet):
    """
    🧬 Mito-Forge - 线粒体基因组学多智能体自动化框架
    
    基于联邦知识系统的专家级生物信息学分析工具
    """
    # 设置上下文
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['quiet'] = quiet
    
    if version:
        console.print(f"Mito-Forge version {__version__}")
        return
    
    if ctx.invoked_subcommand is None:
        print_banner()
        console.print("\n使用 [bold]mito-forge --help[/bold] 查看可用命令")
        console.print("使用 [bold]mito-forge <command> --help[/bold] 查看具体命令帮助\n")

# 注册子命令
main.add_command(pipeline.pipeline)
main.add_command(qc.qc)
main.add_command(assembly.assembly)
main.add_command(annotate.annotate)
main.add_command(doctor.doctor)
main.add_command(config.config)
main.add_command(agents.agents)

if __name__ == '__main__':
    main()