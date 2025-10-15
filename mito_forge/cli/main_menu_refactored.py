"""
重构后的交互式菜单 - 测序类型前置
"""
import click
from pathlib import Path

def run_pipeline_interactive(ctx, lang, t, pipeline):
    """重构的pipeline交互流程 - 测序类型前置"""
    
    # 步骤1: 选择测序类型
    click.echo()
    click.echo("=" * 60)
    click.echo("📊 步骤1: 选择测序类型" if lang != "en" else "📊 Step 1: Select sequencing type")
    click.echo("=" * 60)
    click.echo()
    click.echo("  1) illumina  - Illumina短reads (双端或单端)")
    click.echo("  2) ont       - Oxford Nanopore长reads")
    click.echo("  3) hifi      - PacBio HiFi高保真长reads")
    click.echo("  4) hybrid    - 混合测序 (短reads + 长reads)")
    click.echo("  5) auto      - 自动检测 (推荐)")
    click.echo()
    
    seq_type_choice = click.prompt(
        "测序类型" if lang != "en" else "Sequencing type",
        type=click.Choice(["illumina", "ont", "hifi", "pacbio-hifi", "hybrid", "auto"]),
        default="auto"
    ).strip().lower()
    
    # 支持简写
    if seq_type_choice == "hifi":
        seq_type_choice = "pacbio-hifi"
    
    # 步骤2: 根据测序类型输入文件
    click.echo()
    click.echo("=" * 60)
    click.echo("📁 步骤2: 输入测序文件" if lang != "en" else "📁 Step 2: Input sequencing files")
    click.echo("=" * 60)
    click.echo()
    
    reads = None
    reads2 = None
    long_reads = None
    
    if seq_type_choice in ("illumina", "auto"):
        # Illumina短reads
        from pathlib import Path
        while True:
            reads = click.prompt(
                "R1文件路径" if lang != "en" else "R1 file path",
                default="test.fastq"
            ).strip()
            if Path(reads).is_file():
                break
            else:
                click.echo(f"❌ 文件不存在或不是文件: {reads}" if lang != "en" else f"❌ File not found or not a file: {reads}", err=True)
                click.echo("   请输入正确的文件路径 (不是目录)" if lang != "en" else "   Please enter a valid file path (not a directory)", err=True)
        
        # 自动检测或手动输入R2
        from mito_forge.utils.paired_end_utils import detect_paired_end
        auto_r2 = detect_paired_end(reads)
        if auto_r2:
            use_auto = click.confirm(
                f"检测到R2: {auto_r2}，是否使用?" if lang != "en" else f"Detected R2: {auto_r2}, use it?",
                default=True
            )
            if use_auto:
                reads2 = auto_r2
            else:
                if click.confirm("手动输入R2?" if lang != "en" else "Manually input R2?", default=False):
                    reads2 = click.prompt("R2文件路径" if lang != "en" else "R2 file path").strip()
        else:
            if click.confirm("是否为双端测序?" if lang != "en" else "Paired-end sequencing?", default=False):
                reads2 = click.prompt("R2文件路径" if lang != "en" else "R2 file path").strip()
    
    elif seq_type_choice == "ont":
        # ONT长reads
        click.echo("💡 ONT数据通常是单个长reads文件" if lang != "en" else "💡 ONT data is typically a single long reads file")
        while True:
            reads = click.prompt(
                "ONT长reads文件路径" if lang != "en" else "ONT long reads file path"
            ).strip()
            from pathlib import Path
            if Path(reads).is_file():
                break
            else:
                click.echo(f"❌ 文件不存在或不是文件: {reads}" if lang != "en" else f"❌ File not found or not a file: {reads}", err=True)
                click.echo("   请输入正确的文件路径 (不是目录)" if lang != "en" else "   Please enter a valid file path (not a directory)", err=True)
    
    elif seq_type_choice == "pacbio-hifi":
        # PacBio HiFi长reads
        click.echo("💡 HiFi数据是高保真长reads,通常为.fa或.fastq格式" if lang != "en" else "💡 HiFi data is high-fidelity long reads, typically .fa or .fastq format")
        while True:
            reads = click.prompt(
                "HiFi长reads文件路径" if lang != "en" else "HiFi long reads file path"
            ).strip()
            from pathlib import Path
            if Path(reads).is_file():
                break
            else:
                click.echo(f"❌ 文件不存在或不是文件: {reads}" if lang != "en" else f"❌ File not found or not a file: {reads}", err=True)
                click.echo("   请输入正确的文件路径 (不是目录)" if lang != "en" else "   Please enter a valid file path (not a directory)", err=True)
    
    elif seq_type_choice == "hybrid":
        # 混合测序
        click.echo("💡 混合测序需要:")
        click.echo("   - 短reads (Illumina R1 + R2)")
        click.echo("   - 长reads (ONT或PacBio)")
        click.echo()
        reads = click.prompt("短reads R1路径" if lang != "en" else "Short reads R1 path").strip()
        reads2 = click.prompt("短reads R2路径" if lang != "en" else "Short reads R2 path").strip()
        long_reads = click.prompt("长reads路径 (ONT/PacBio)" if lang != "en" else "Long reads path (ONT/PacBio)").strip()
    
    # 步骤3: 基本配置
    click.echo()
    click.echo("=" * 60)
    click.echo("⚙️  步骤3: 基本配置" if lang != "en" else "⚙️  Step 3: Basic configuration")
    click.echo("=" * 60)
    click.echo()
    
    output = click.prompt(
        "输出目录" if lang != "en" else "Output directory",
        default="user_analysis_results"
    ).strip()
    
    kingdom = click.prompt(
        "物种类型" if lang != "en" else "Kingdom",
        type=click.Choice(["animal", "plant"]),
        default="animal"
    )
    
    interactive_mode = click.confirm(
        "启用交互式错误处理?" if lang != "en" else "Enable interactive error handling?",
        default=True
    )
    
    threads = click.prompt(
        "线程数" if lang != "en" else "Threads",
        type=int,
        default=8
    )
    
    # 步骤4: 工具选择(可选)
    click.echo()
    click.echo("=" * 60)
    click.echo("🔧 步骤4: 工具选择 (可选)" if lang != "en" else "🔧 Step 4: Tool selection (optional)")
    click.echo("=" * 60)
    click.echo()
    
    if seq_type_choice == "auto":
        click.echo("💡 提示: 已选择'auto',将根据文件自动检测并使用默认工具")
        click.echo("         如需手动选择工具,请在下一步选择'y'")
        click.echo()
    
    choose_tools = click.confirm(
        "是否手动选择工具?" if lang != "en" else "Manually select tools?",
        default=False
    )
    
    # 准备kwargs
    kwargs = {
        "reads": reads,
        "reads2": reads2,
        "long_reads": long_reads,
        "output": output,
        "kingdom": kingdom,
        "threads": threads,
        "verbose": False,
        "resume": None,
        "checkpoint": None,
        "config_file": None,
        "interactive": interactive_mode,
        "lang": lang,
        "detail_level": "quick",
        "seq_type": seq_type_choice if seq_type_choice != "auto" else None,
    }
    
    if choose_tools:
        # 手动选择工具
        click.echo()
        click.echo("=" * 60)
        click.echo("🔧 步骤5: 选择具体工具" if lang != "en" else "🔧 Step 5: Select specific tools")
        click.echo("=" * 60)
        click.echo()
        
        # 如果是auto,需要先确定实际类型
        actual_type = seq_type_choice
        if actual_type == "auto":
            # 根据已输入文件自动检测
            from mito_forge.utils.selection import detect_seq_type as sel_detect_seq_type
            actual_type = sel_detect_seq_type([reads])
            click.echo(f"🔍 自动检测到测序类型: {actual_type}")
            click.echo()
        
        kg_norm = kingdom.strip().lower()
        
        # 根据类型显示可用工具
        if actual_type in ("illumina",):
            asm_list = [
                "GetOrganelle", "NOVOPlasty", "MitoZ", "MITObim", "MToolBox",
                "mitoMaker", "ARC", "IDBA-UD", "Velvet", "SPAdes", "MEANGS"
            ]
            if kg_norm == "plant":
                asm_list += ["SOAPdenovo2", "GSAT"]
            qc_list = ["fastqc"]
        
        elif actual_type == "ont":
            asm_list = ["Flye", "Canu", "Raven", "Shasta", "wtdbg2", "Miniasm+Minipolish"]
            if kg_norm == "plant":
                asm_list += ["SMARTdenovo", "NextDenovo", "PLCL", "Oatk", "POLAP"]
            qc_list = ["NanoPlot"]
        
        elif actual_type == "pacbio-hifi":
            asm_list = ["Hifiasm", "Flye", "Peregrine"]
            if kg_norm == "animal":
                asm_list = ["MitoHiFi"] + asm_list
            if kg_norm == "plant":
                asm_list = ["PMAT"] + asm_list
            qc_list = ["basic_stats"]
        
        elif actual_type == "hybrid":
            asm_list = ["Unicycler", "SPAdes", "Flye", "MaSuRCA"]
            qc_list = ["fastqc", "NanoPlot"]
        
        else:
            asm_list = ["SPAdes"]
            qc_list = ["fastqc"]
        
        click.echo("可选组装器: " + ", ".join(asm_list))
        assembler = click.prompt(
            "选择组装器" if lang != "en" else "Choose assembler",
            default=asm_list[0]
        )
        
        click.echo("可选QC: " + ", ".join(qc_list))
        qc_choice = click.prompt(
            "选择QC (留空跳过)" if lang != "en" else "Choose QC (leave empty to skip)",
            default="",
            show_default=False
        ).strip()
        
        # 生成工具计划
        try:
            import json as _json
            plan_path = Path(output) / "tool_plan.json"
            plan = {"tool_plan": {"assembler": {"name": assembler}}}
            if qc_choice:
                plan["tool_plan"]["qc"] = [qc_choice]
            plan_path.parent.mkdir(parents=True, exist_ok=True)
            plan_path.write_text(_json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
            
            kwargs["config_file"] = str(plan_path)
            kwargs["seq_type"] = actual_type
            
            click.echo()
            click.echo(f"✅ 已选择工具: assembler={assembler}" + (f", qc={qc_choice}" if qc_choice else ""))
            click.echo(f"📄 工具计划文件: {plan_path}")
        except Exception as e:
            click.echo(f"⚠️  写入工具计划失败: {e}")
    
    # 执行pipeline
    click.echo()
    click.echo("=" * 60)
    click.echo("🚀 开始执行流水线" if lang != "en" else "🚀 Starting pipeline")
    click.echo("=" * 60)
    click.echo()
    
    ctx.invoke(pipeline, **kwargs)
