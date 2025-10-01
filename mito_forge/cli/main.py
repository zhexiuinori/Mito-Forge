"""
Mito-Forge CLI 主入口 (LangGraph Edition)
"""
import click
from pathlib import Path
from .commands.pipeline import pipeline, status
from .commands.doctor import doctor
from .commands.config import config
from .commands.model import model
from .commands.agents import agents
from .commands.qc import qc
from .commands.assembly import assembly
from .commands.annotate import annotate

@click.group()
@click.version_option(version="0.2.0", prog_name="mito-forge")
@click.option("--lang", type=click.Choice(["zh","en"]), default="zh", help="输出语言")
@click.pass_context
def cli(ctx, lang):
    """
    🧬 Mito-Forge: 基于 LangGraph 的智能线粒体基因组组装工具
    
    一个使用多智能体协作的线粒体基因组分析流水线：
    
    \b
    • Supervisor Agent: 智能分析数据并制定执行策略
    • QC Agent: 自动质量控制和数据清理  
    • Assembly Agent: 多工具组装策略选择
    • Annotation Agent: 基因功能注释
    • Report Agent: 综合结果报告生成
    
    支持状态机编排、检查点恢复、失败重试等高级功能。
    """
    # 将语言保存为全局环境变量，供子命令读取
    import os
    if lang:
        os.environ["MITO_LANG"] = lang
    # 确保 ctx.obj 存在
    ctx.ensure_object(dict)
    # 无子命令时进入交互式菜单
    if ctx.invoked_subcommand is None:
        _menu(ctx)

# 注册命令
cli.add_command(pipeline, name="pipeline")
cli.add_command(status, name="status") 
cli.add_command(doctor, name="doctor")
cli.add_command(config, name="config")
cli.add_command(model, name="model")
cli.add_command(agents, name="agents")
cli.add_command(qc, name="qc")
cli.add_command(assembly, name="assembly")
cli.add_command(annotate, name="annotate")

# 添加快捷命令别名
@cli.command()
@click.pass_context
def run(ctx, **kwargs):
    """运行流水线 (pipeline 命令的别名)"""
    ctx.invoke(pipeline, **kwargs)

@cli.command()
@click.pass_context
def menu(ctx):
    """进入交互式菜单"""
    _menu(ctx)


def _menu(ctx):
    """简单交互式菜单，不需用户记命令行参数"""
    import os
    lang = os.getenv("MITO_LANG", "zh")
    texts = {
        "zh": {
            "title": "=== Mito-Forge 菜单 ===",
            "run_pipeline": "1) 运行流水线",
            "agents": "2) 智能体管理",
            "doctor": "3) 系统诊断",
            "config": "4) 配置管理",
            "status_checkpoint": "5) 查看流水线状态（检查点）",
            "exit": "6) 退出",
            "choose": "请选择功能编号",
            "prompt_reads": "输入测序文件路径",
            "prompt_output": "输出目录",
            "prompt_kingdom": "物种类型 (animal/plant)",
            "prompt_interactive": "启用交互式错误处理 (--interactive)?",
            "prompt_threads": "线程数",
            "prompt_checkpoint": "请输入检查点文件路径",
            "bye": "已退出。",
            "invalid": "无效选择，请重试。"
        },
        "en": {
            "title": "=== Mito-Forge Menu ===",
            "run_pipeline": "1) Run pipeline",
            "agents": "2) Manage agents",
            "doctor": "3) System doctor",
            "config": "4) Config management",
            "status_checkpoint": "5) View pipeline status (checkpoint)",
            "exit": "6) Exit",
            "choose": "Choose a number",
            "prompt_reads": "Reads file path",
            "prompt_output": "Output directory",
            "prompt_kingdom": "Kingdom (animal/plant)",
            "prompt_interactive": "Enable interactive error handling (--interactive)?",
            "prompt_threads": "Threads",
            "prompt_checkpoint": "Enter checkpoint file path",
            "bye": "Bye.",
            "invalid": "Invalid choice, please retry."
        }
    }
    t = texts.get(lang, texts["zh"])
    while True:
        click.echo(t["title"])
        click.echo(t["run_pipeline"])
        click.echo(t["agents"])
        click.echo(t["doctor"])
        click.echo(t["config"])
        click.echo(t["status_checkpoint"])
        click.echo(t["exit"])
        choice = click.prompt(t["choose"], type=int, default=1)

        if choice == 1:
            # 运行流水线：最小参数引导；更复杂参数可后续扩展
            reads = click.prompt(t["prompt_reads"], default="test.fastq")
            output = click.prompt(t["prompt_output"], default="user_analysis_results")
            kingdom = click.prompt(t["prompt_kingdom"], default="animal")
            interactive = click.confirm(t["prompt_interactive"], default=True)
            threads = click.prompt(t["prompt_threads"], type=int, default=8)
            kwargs = {
                "reads": reads,
                "output": output,
                "kingdom": kingdom,
                "threads": threads,
                "verbose": False,
                "resume": None,
                "checkpoint": None,
                "config_file": None,
                "interactive": interactive,
            }
            ctx.invoke(pipeline, **kwargs)
        elif choice == 2:
            # 智能体管理
            detailed = click.confirm("显示详细信息?", default=False)
            ctx.invoke(agents, status=True, detailed=detailed, restart=None)
        elif choice == 3:
            # 系统诊断
            ctx.invoke(doctor)
        elif choice == 4:
            # 配置管理（只读显示）
            ctx.invoke(config)
        elif choice == 5:
            # 查看流水线状态（检查点）
            cp_default = str(Path("user_analysis_results") / "work" / "checkpoint.json")
            cp = click.prompt(t["prompt_checkpoint"], default=cp_default)
            ctx.invoke(status, checkpoint=cp)
        elif choice == 6:
            click.echo(t["bye"])
            break
        else:
            click.echo(t["invalid"])

if __name__ == "__main__":
    cli()