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

# 读取环境语言并提供简单翻译
import os
def _t(key):
    lang = os.getenv("MITO_LANG", "zh")
    texts = {
        "zh": {
            "title": "🤖 智能体系统状态",
            "list": "智能体状态列表:",
            "status": "状态",
            "type": "类型",
            "tasks": "任务数",
            "mem_last": "内存使用",
            "last_activity": "最后活动",
            "summary": "📊 系统摘要:",
            "active_agents": "活跃智能体",
            "total_tasks": "总任务数",
            "cap_desc": "📋 [bold]智能体功能说明[/bold]",
            "restart_ok": "智能体 {name} 重启成功",
            "restart_fail": "智能体 {name} 重启失败",
            "error": "错误",
            "unexpected": "未预期的错误"
        },
        "en": {
            "title": "🤖 Agents System Status",
            "list": "Agents status list:",
            "status": "Status",
            "type": "Type",
            "tasks": "Tasks",
            "mem_last": "Memory",
            "last_activity": "Last activity",
            "summary": "📊 Summary:",
            "active_agents": "Active agents",
            "total_tasks": "Total tasks",
            "cap_desc": "📋 [bold]Agents capabilities[/bold]",
            "restart_ok": "Agent {name} restarted",
            "restart_fail": "Agent {name} restart failed",
            "error": "Error",
            "unexpected": "Unexpected error"
        }
    }
    return texts.get(lang, texts["zh"]).get(key, key)

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
                    console.print(f"✅ [bold green]{_t('restart_ok').format(name=restart)}[/bold green]")
            else:
                console.print(f"❌ [bold red]{_t('restart_fail').format(name=restart)}[/bold red]")
                return 1
        
        # 显示智能体状态
        if status or not restart:
            _display_agents_status(orchestrator, detailed, quiet)
        
        return 0
        
    except MitoForgeError as e:
        console.print(f"\n❌ [bold red]{_t('error')}:[/bold red] {e}")
        if verbose:
            console.print_exception()
        return 1
    except Exception as e:
        console.print(f"\n💥 [bold red]{_t('unexpected')}:[/bold red] {e}")
        if verbose:
            console.print_exception()
        return 1

def _display_agents_status(orchestrator, detailed, quiet):
    """显示智能体状态"""
    if quiet:
        return
    
    console.print(f"\n[bold blue]{_t('title')}[/bold blue]\n")
    
    # 获取智能体信息
    agents_info = orchestrator.get_agents_status()
    
    # 使用简单文本格式显示智能体状态
    console.print(_t("list"))
    console.print("=" * 70)
    
    for agent_name, info in agents_info.items():
        status_icon = "🟢" if info['status'] == 'active' else "🔴" if info['status'] == 'error' else "🟡"
        status_text = f"{status_icon} {info['status']}"
        
        console.print(f"• {agent_name:<15} | {_t('status')}: {status_text:<12} | {_t('type')}: {info['type']:<18} | {_t('tasks')}: {info['task_count']}")
        
        if detailed:
            console.print(f"  └─ {_t('mem_last')}: {info.get('memory_usage', 0):.1f}MB | {_t('last_activity')}: {info.get('last_activity', 'N/A')}")
    
    console.print("=" * 70)
    
    # 显示系统摘要
    active_count = sum(1 for info in agents_info.values() if info['status'] == 'active')
    total_count = len(agents_info)
    
    console.print(f"\n{_t('summary')}")
    console.print(f"   {_t('active_agents')}: {active_count}/{total_count}")
    
    if detailed:
        total_tasks = sum(info['task_count'] for info in agents_info.values())
        console.print(f"   {_t('total_tasks')}: {total_tasks}")
    
    # 显示智能体描述
    if detailed:
        console.print(f"\n{_t('cap_desc')}")
        descriptions = {
            "supervisor": "🎯 总指挥 - 协调和管理所有智能体",
            "qc": "🔍 质控专家 - 数据质量评估和预处理",
            "assembly": "🧬 组装专家 - 基因组序列组装",
            "annotation": "📝 注释专家 - 基因功能注释",
            "analysis": "📊 分析专家 - 系统发育和比较分析"
        }
        
        for agent_name, description in descriptions.items():
            if agent_name in agents_info:
                console.print(f"  {description}")