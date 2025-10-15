"""
工具环境设置命令
"""
import click
from rich.console import Console
from rich.table import Table
from pathlib import Path
from ...utils.tool_env_manager import ToolEnvironmentManager

console = Console()


@click.group(name="tools")
def tools_group():
    """工具环境管理命令"""
    pass


@tools_group.command(name="list-envs")
def list_envs():
    """列出所有可用的工具环境配置"""
    console.print("\n[bold cyan]📦 可用的工具环境配置[/bold cyan]\n")
    
    env_mgr = ToolEnvironmentManager()
    available = env_mgr.list_available_envs()
    
    if not available:
        console.print("[yellow]没有找到环境配置文件[/yellow]")
        return
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("工具名称", style="cyan")
    table.add_column("环境名称", style="green")
    table.add_column("状态", style="yellow")
    
    for tool in available:
        info = env_mgr.get_env_info(tool)
        status = "✅ 已安装" if info["exists"] else "❌ 未安装"
        table.add_row(tool, info["env_name"], status)
    
    console.print(table)
    console.print()


@tools_group.command(name="setup-env")
@click.argument("tool_name")
@click.option("--force", is_flag=True, help="强制重建已存在的环境")
def setup_env(tool_name: str, force: bool):
    """为指定工具创建conda环境"""
    console.print(f"\n[bold cyan]🔧 设置 {tool_name} 的环境[/bold cyan]\n")
    
    env_mgr = ToolEnvironmentManager()
    
    # 检查配置文件是否存在
    yaml_file = env_mgr.get_env_yaml(tool_name)
    if not yaml_file:
        console.print(f"[red]❌ 未找到 {tool_name} 的环境配置文件[/red]")
        console.print(f"[yellow]配置文件应该位于: {env_mgr.envs_dir}/{tool_name}_env.yaml[/yellow]")
        return
    
    # 创建环境
    with console.status(f"[bold green]正在创建环境...这可能需要几分钟"):
        success = env_mgr.create_env(tool_name, force=force)
    
    if success:
        console.print(f"[green]✅ 成功创建环境: {env_mgr.get_env_name(tool_name)}[/green]")
        console.print(f"\n[cyan]💡 提示: 工具将自动使用此环境[/cyan]")
    else:
        console.print(f"[red]❌ 创建环境失败,请查看上方错误信息[/red]")


@tools_group.command(name="setup-all")
@click.option("--force", is_flag=True, help="强制重建已存在的环境")
def setup_all(force: bool):
    """为所有工具创建conda环境"""
    console.print("\n[bold cyan]🔧 批量设置工具环境[/bold cyan]\n")
    
    env_mgr = ToolEnvironmentManager()
    available = env_mgr.list_available_envs()
    
    if not available:
        console.print("[yellow]没有找到环境配置文件[/yellow]")
        return
    
    console.print(f"[cyan]找到 {len(available)} 个工具配置[/cyan]\n")
    
    success_count = 0
    failed = []
    
    for tool in available:
        # 跳过已存在的环境(除非force)
        if env_mgr.env_exists(tool) and not force:
            console.print(f"[yellow]⏭️  {tool}: 环境已存在,跳过[/yellow]")
            success_count += 1
            continue
        
        console.print(f"[cyan]🔧 正在设置 {tool}...[/cyan]")
        
        with console.status(f"[bold green]创建中..."):
            success = env_mgr.create_env(tool, force=force)
        
        if success:
            console.print(f"[green]✅ {tool}: 成功[/green]")
            success_count += 1
        else:
            console.print(f"[red]❌ {tool}: 失败[/red]")
            failed.append(tool)
    
    # 总结
    console.print(f"\n[bold]{'='*50}[/bold]")
    console.print(f"[green]✅ 成功: {success_count}/{len(available)}[/green]")
    if failed:
        console.print(f"[red]❌ 失败: {', '.join(failed)}[/red]")
    console.print(f"[bold]{'='*50}[/bold]\n")


@tools_group.command(name="env-info")
@click.argument("tool_name")
def env_info(tool_name: str):
    """显示工具环境的详细信息"""
    env_mgr = ToolEnvironmentManager()
    info = env_mgr.get_env_info(tool_name)
    
    console.print(f"\n[bold cyan]ℹ️  {tool_name} 环境信息[/bold cyan]\n")
    
    table = Table(show_header=False, box=None)
    table.add_column("属性", style="cyan")
    table.add_column("值", style="green")
    
    table.add_row("工具名称", info["tool_name"])
    table.add_row("环境名称", info["env_name"])
    table.add_row("配置文件", info["yaml_file"] or "未找到")
    table.add_row("安装状态", "✅ 已安装" if info["exists"] else "❌ 未安装")
    
    console.print(table)
    console.print()
