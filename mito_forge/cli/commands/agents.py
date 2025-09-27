"""
Agents 命令

智能体状态管理
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ...core.agents.orchestrator import Orchestrator
from ...utils.config import Config
from ...utils.exceptions import MitoForgeError

console = Console()

@click.command()
@click.option('--status', is_flag=True, help='显示智能体状态')
@click.option('--detailed', is_flag=True, help='显示详细信息')
@click.option('--restart', help='重启指定智能体')
@click.pass_context
def agents(ctx, status, detailed, restart):
    """
    智能体状态管理
    
    查看和管理Mito-Forge智能体系统
    
    示例:
        mito-forge agents
        mito-forge agents --detailed
        mito-forge agents --restart qc_agent
    """
    verbose = ctx.obj.get('verbose', False)
    quiet = ctx.obj.get('quiet', False)
    
    try:
        # 初始化编排器
        config = Config()
        orchestrator = Orchestrator(config)
        
        # 重启智能体
        if restart:
            result = orchestrator.restart_agent(restart)
            if result:
                if not quiet:
                    console.print(f"✅ [bold green]智能体 {restart} 重启成功[/bold green]")
            else:
                console.print(f"❌ [bold red]智能体 {restart} 重启失败[/bold red]")
                return 1
        
        # 显示智能体状态
        if status or not restart:
            _display_agents_status(orchestrator, detailed, quiet)
        
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

def _display_agents_status(orchestrator, detailed, quiet):
    """显示智能体状态"""
    if quiet:
        return
    
    console.print("\n🤖 [bold blue]智能体系统状态[/bold blue]\n")
    
    # 获取智能体信息
    agents_info = orchestrator.get_agents_status()
    
    # 创建状态表格
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("智能体", style="cyan")
    table.add_column("状态", justify="center")
    table.add_column("类型", style="green")
    table.add_column("任务数", justify="right")
    
    if detailed:
        table.add_column("内存使用", justify="right")
        table.add_column("最后活动", style="dim")
    
    for agent_name, info in agents_info.items():
        status_icon = "🟢" if info['status'] == 'active' else "🔴" if info['status'] == 'error' else "🟡"
        status_text = f"{status_icon} {info['status']}"
        
        row = [
            agent_name,
            status_text,
            info['type'],
            str(info['task_count'])
        ]
        
        if detailed:
            row.extend([
                f"{info.get('memory_usage', 0):.1f}MB",
                info.get('last_activity', 'N/A')
            ])
        
        table.add_row(*row)
    
    console.print(table)
    
    # 显示系统摘要
    active_count = sum(1 for info in agents_info.values() if info['status'] == 'active')
    total_count = len(agents_info)
    
    summary = f"活跃智能体: {active_count}/{total_count}"
    if detailed:
        total_tasks = sum(info['task_count'] for info in agents_info.values())
        summary += f"\n总任务数: {total_tasks}"
    
    panel = Panel(
        summary,
        title="系统摘要",
        border_style="green" if active_count == total_count else "yellow"
    )
    console.print(panel)
    
    # 显示智能体描述
    if detailed:
        console.print("\n📋 [bold]智能体功能说明[/bold]")
        descriptions = {
            "orchestrator": "🎯 总指挥 - 协调和管理所有智能体",
            "qc_agent": "🔍 质控专家 - 数据质量评估和预处理",
            "assembly_agent": "🧬 组装专家 - 基因组序列组装",
            "annotation_agent": "📝 注释专家 - 基因功能注释",
            "analysis_agent": "📊 分析专家 - 系统发育和比较分析"
        }
        
        for agent_name, description in descriptions.items():
            if agent_name in agents_info:
                console.print(f"  {description}")