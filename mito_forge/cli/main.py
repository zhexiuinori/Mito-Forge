"""
Mito-Forge CLI 主入口 (LangGraph Edition)
"""
import click
from .commands.doctor import doctor
from pathlib import Path
import os
from .commands.pipeline import pipeline, status
from .commands.doctor import doctor
from .commands.config import config
from .commands.model import model
from .commands.agents import agents
from .commands.qc import qc
from .commands.assembly import assembly
from .commands.annotate import annotate
from .commands.tools_setup import tools_group
from .commands.resume import resume

class MitoGroup(click.Group):
    """自定义分组：默认仅显示核心命令；--expert 时显示全部命令"""
    core_commands = {"pipeline", "status", "doctor", "menu", "run"}

    def list_commands(self, ctx):
        # 使用父类提供的顺序（已按添加顺序）
        names = super().list_commands(ctx)
        # 如果带 --expert，则显示全部（从多渠道判断，避免帮助阶段获取不到参数）
        expert_on = False
        if ctx:
            if getattr(ctx, "params", None) and ctx.params.get("expert"):
                expert_on = True
            elif getattr(ctx, "obj", None) and ctx.obj.get("expert"):
                expert_on = True
        if not expert_on and os.environ.get("MITO_EXPERT") == "1":
            expert_on = True
        if expert_on:
            return names
        # 默认仅显示核心命令
        return [n for n in names if n in self.core_commands]

def _expert_cb(ctx, param, value):
    # 早期回调，确保在帮助渲染前就记录 expert 状态
    if value:
        os.environ["MITO_EXPERT"] = "1"
        ctx.ensure_object(dict)
        ctx.obj["expert"] = True
    return value

@click.group(cls=MitoGroup)
@click.version_option(version="0.2.0", prog_name="mito-forge")
@click.option("--lang", type=click.Choice(["zh","en"]), default="zh", help="输出语言")
@click.option("--expert", is_flag=True, is_eager=True, expose_value=True, callback=_expert_cb, help="显示高级命令")
@click.pass_context
def cli(ctx, lang, expert):
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
cli.add_command(tools_group, name="tools")
cli.add_command(resume, name="resume")

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
            # 使用重构的pipeline交互流程
            from .main_menu_refactored import run_pipeline_interactive
            run_pipeline_interactive(ctx, lang, t, pipeline)
            continue  # 返回主菜单
            
            # 以下是旧代码(已被上面替代)
            """
            OLD_CODE_START_MARKER
        if choice == 1_OLD:
            # 运行流水线：最小参数引导；可选“工具选择”
            reads = click.prompt(t["prompt_reads"], default="test.fastq").strip()
            
            # 双端测序支持：自动检测或手动输入
            reads2 = None
            from mito_forge.utils.paired_end_utils import detect_paired_end
            auto_r2 = detect_paired_end(reads)
            if auto_r2:
                use_auto = click.confirm(
                    ("检测到双端数据 R2: {}，是否使用?" if lang != "en" else "Detected R2: {}, use it?").format(auto_r2),
                    default=True
                )
                if use_auto:
                    reads2 = auto_r2
                else:
                    if click.confirm(("手动输入 R2 文件?" if lang != "en" else "Manually input R2?"), default=False):
                        reads2 = click.prompt(("R2 文件路径" if lang != "en" else "R2 file path")).strip()
            else:
                if click.confirm(("是否为双端测序?" if lang != "en" else "Paired-end sequencing?"), default=False):
                    reads2 = click.prompt(("R2 文件路径" if lang != "en" else "R2 file path")).strip()
            
            output = click.prompt(t["prompt_output"], default="user_analysis_results").strip()
            kingdom = click.prompt(t["prompt_kingdom"], type=click.Choice(["animal", "plant"]), default="animal")
            interactive = click.confirm(t["prompt_interactive"], default=True)
            threads = click.prompt(t["prompt_threads"], type=int, default=8)

            # 是否选择工具（保持菜单简单，不影响不选择的用户）
            choose_tools = click.confirm(("是否选择工具?" if lang != "en" else "Choose tools?"), default=False)

            # 统一 kwargs，后面根据是否选择工具再补充
            kwargs = {
                "reads": reads,
                "reads2": reads2,  # 添加 R2 支持
                "long_reads": None,  # 初始化为None，hybrid模式会更新
                "output": output,
                "kingdom": kingdom,
                "threads": threads,
                "verbose": False,
                "resume": None,
                "checkpoint": None,
                "config_file": None,
                "interactive": interactive,
            }

            if choose_tools:
                # 选择测序类型与组装器（按 seq-type/kingdom 动态过滤常用集合，覆盖你的清单）
                seqtype = click.prompt(("测序类型 (auto/illumina/ont/pacbio-hifi/pacbio-clr/hybrid)" if lang != "en" else "Seq type (auto/illumina/ont/pacbio-hifi/pacbio-clr/hybrid)"), default="auto").strip().lower()
                # 支持简写: hifi -> pacbio-hifi, clr -> pacbio-clr
                if seqtype == "hifi":
                    seqtype = "pacbio-hifi"
                elif seqtype == "clr":
                    seqtype = "pacbio-clr"
                
                # Hybrid模式需要额外的长reads输入
                long_reads = None
                if seqtype == "hybrid":
                    click.echo(("💡 混合测序模式需要短reads和长reads" if lang != "en" else "💡 Hybrid mode requires both short and long reads"))
                    click.echo(("  已输入短reads: {}".format(reads) if lang != "en" else "  Short reads: {}".format(reads)))
                    if reads2:
                        click.echo(("  短reads R2: {}".format(reads2) if lang != "en" else "  Short reads R2: {}".format(reads2)))
                    long_reads = click.prompt(("  请输入长reads路径 (ONT/PacBio)" if lang != "en" else "  Long reads path (ONT/PacBio)")).strip()
                
                kg_norm = (kingdom or "animal").strip().lower()

                if seqtype in ("illumina", "auto"):
                    asm_list = [
                        "GetOrganelle", "NOVOPlasty", "MitoZ", "MITObim", "MToolBox",
                        "mitoMaker", "ARC", "IDBA-UD", "Velvet", "SPAdes", "MEANGS"
                    ]
                    # 植物专用补充
                    if kg_norm == "plant":
                        asm_list += ["SOAPdenovo2", "GSAT"]
                    # 真菌补充
                    if kg_norm == "fungi":
                        asm_list = ["Norgal", "SPAdes", "NOVOPlasty", "MITObim"] + [x for x in asm_list if x not in {"Norgal","SPAdes","NOVOPlasty","MITObim"}]
                    qc_list = ["fastqc"]

                elif seqtype == "ont":
                    asm_list = ["Flye", "Canu", "Raven", "Shasta", "wtdbg2", "Miniasm+Minipolish"]
                    if kg_norm == "plant":
                        asm_list += ["SMARTdenovo", "NextDenovo", "PLCL", "Oatk", "POLAP"]
                    qc_list = ["NanoPlot"]

                elif seqtype == "pacbio-hifi":
                    asm_list = ["Hifiasm", "Flye", "Peregrine"]
                    if kg_norm == "animal":
                        asm_list = ["MitoHiFi"] + asm_list
                    if kg_norm == "plant":
                        asm_list = ["PMAT"] + asm_list
                    qc_list = ["basic_stats"]

                elif seqtype == "pacbio-clr":
                    asm_list = ["Canu", "Flye", "wtdbg2", "Miniasm+Minipolish"]
                    qc_list = ["basic_stats"]

                elif seqtype == "hybrid":
                    asm_list = ["Unicycler", "SPAdes", "Flye", "MaSuRCA"]
                    qc_list = ["fastqc", "NanoPlot"]

                else:
                    asm_list = ["SPAdes"]
                    qc_list = ["fastqc"]

                click.echo(("可选组装器: " if lang != "en" else "Assemblers: ") + ", ".join(asm_list))
                assembler = click.prompt(("选择组装器" if lang != "en" else "Choose assembler"), default=asm_list[0])

                click.echo(("可选QC: " if lang != "en" else "QC options: ") + ", ".join(qc_list))
                qc_choice = click.prompt(("选择QC(可选，留空跳过)" if lang != "en" else "Choose QC (optional, leave empty to skip)"), default="", show_default=False).strip()

                # 生成工具计划文件到输出目录
                try:
                    import json as _json
                    plan_path = Path(output) / "tool_plan.json"
                    plan = {"tool_plan": {"assembler": {"name": assembler}}}
                    if qc_choice:
                        plan["tool_plan"]["qc"] = [qc_choice]
                    plan_path.parent.mkdir(parents=True, exist_ok=True)
                    plan_path.write_text(_json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

                    # 使用配置文件运行，并传递测序类型
                    kwargs["config_file"] = str(plan_path)
                    kwargs["seq_type"] = seqtype
                    
                    # 如果是hybrid模式，传递long_reads
                    if seqtype == "hybrid" and long_reads:
                        kwargs["long_reads"] = long_reads

                    # 明确反馈选择结果与配置文件位置
                    click.echo(("✅ 已选择工具: " if lang != "en" else "✅ Selected tools: ") + f"assembler={assembler}" + (f", qc={qc_choice}" if qc_choice else ""))
                    click.echo(("📄 工具计划文件: " if lang != "en" else "📄 Tool plan file: ") + f"{plan_path}")
                except Exception as _e:
                    # 写文件失败时，仍按不选择工具的方式运行
                    click.echo(("⚠️ 写入工具计划失败，将按默认工具运行: " if lang != "en" else "⚠️ Failed to write tool plan, running with defaults: ") + f"{_e}")

            ctx.invoke(pipeline, **kwargs)
            """
            # OLD_CODE_END_MARKER
        elif choice == 2:
            # 智能体管理
            detailed = click.confirm("显示详细信息?", default=False)
            ctx.invoke(agents, status=True, detailed=detailed, restart=None)
        elif choice == 3:
            # 系统诊断
            click.echo()
            click.echo(("=" * 50) if lang != "en" else ("=" * 50))
            click.echo(("系统诊断" if lang != "en" else "System Doctor"))
            click.echo(("=" * 50) if lang != "en" else ("=" * 50))
            
            # 询问是否自动修复
            auto_fix = click.confirm(
                ("是否自动安装缺失的工具?" if lang != "en" else "Auto-install missing tools?"),
                default=False
            )
            
            # 调用 doctor 命令（使用默认工具列表）
            from mito_forge.utils.toolcheck import DEFAULT_TOOLS
            default_tools_str = ",".join(DEFAULT_TOOLS)
            ctx.invoke(doctor, tools=default_tools_str, fix=auto_fix)
            
            click.echo()
            input(("按 Enter 继续..." if lang != "en" else "Press Enter to continue..."))
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

main = cli

if __name__ == "__main__":
    cli()