"""
Config 命令

配置管理
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ...utils.config import Config
from ...utils.exceptions import MitoForgeError

console = Console()

@click.command()
@click.option('--show', is_flag=True, help='显示当前配置')
@click.option('--set', 'set_config', nargs=2, multiple=True, 
              metavar='KEY VALUE', help='设置配置项')
@click.option('--reset', is_flag=True, help='重置为默认配置')
@click.option('--config-file', type=click.Path(), 
              help='指定配置文件路径')
@click.pass_context
def config(ctx, show, set_config, reset, config_file):
    """
    配置管理
    
    管理Mito-Forge的配置参数
    
    示例:
        mito-forge config --show
        mito-forge config --set threads 8
        mito-forge config --set assembler spades
    """
    verbose = ctx.obj.get('verbose', False)
    quiet = ctx.obj.get('quiet', False)
    
    try:
        # 加载配置
        config_obj = Config(config_file) if config_file else Config()
        
        # 重置配置
        if reset:
            config_obj.reset_to_defaults()
            if not quiet:
                console.print("✅ [bold green]配置已重置为默认值[/bold green]")
        
        # 设置配置项
        if set_config:
            for key, value in set_config:
                config_obj.set(key, value)
                if not quiet:
                    console.print(f"✅ 设置 {key} = {value}")
        
        # 显示配置
        if show or not set_config and not reset:
            _display_config(config_obj, quiet)
        
        # 保存配置
        if set_config or reset:
            config_obj.save()
            if not quiet:
                console.print(f"\n💾 配置已保存到: {config_obj.config_file}")
        
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

def _display_config(config_obj, quiet):
    """显示配置信息"""
    if quiet:
        return
    
    console.print("\n⚙️  [bold blue]Mito-Forge 配置[/bold blue]\n")
    
    # 创建配置表格
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("配置项", style="cyan")
    table.add_column("当前值", style="green")
    table.add_column("描述", style="dim")
    
    config_items = [
        ("threads", "线程数"),
        ("memory", "内存限制"),
        ("quality_threshold", "质量阈值"),
        ("assembler", "默认组装器"),
        ("annotation_tool", "默认注释工具"),
        ("output_dir", "默认输出目录"),
        ("log_level", "日志级别"),
        ("temp_dir", "临时目录"),
    ]
    
    for key, description in config_items:
        value = config_obj.get(key, "未设置")
        table.add_row(key, str(value), description)
    
    console.print(table)
    
    # 显示配置文件路径
    panel = Panel(
        f"配置文件: [bold]{config_obj.config_file}[/bold]\n"
        f"使用 [bold]mito-forge config --set KEY VALUE[/bold] 修改配置",
        title="配置信息",
        border_style="blue"
    )
    console.print(panel)