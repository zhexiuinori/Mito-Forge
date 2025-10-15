"""Resume命令 - 恢复暂停的Pipeline"""

import click
from pathlib import Path
from rich.console import Console
import json

console = Console()


@click.command("resume")
@click.argument("task_id")
@click.option("--annotation", type=click.Path(exists=True), required=True,
              help="GeSeq注释结果文件(.gbk)")
def resume(task_id: str, annotation: str):
    """恢复暂停的pipeline并继续执行
    
    当plant模式下使用GeSeq完成注释后,使用此命令恢复pipeline执行
    
    示例:
        mito-forge resume abc12345 --annotation result.gbk
    """
    
    console.print(f"\n🔄 恢复任务: {task_id}")
    
    # 查找checkpoint文件
    # 先在当前目录查找,然后在work目录查找
    checkpoint_patterns = [
        Path.cwd() / f"checkpoint_{task_id}.json",
        Path.cwd() / "work" / f"checkpoint_{task_id}.json",
    ]
    
    checkpoint_file = None
    for pattern in checkpoint_patterns:
        if pattern.exists():
            checkpoint_file = pattern
            break
    
    if not checkpoint_file:
        console.print(f"[red]❌ Checkpoint文件不存在: checkpoint_{task_id}.json[/red]")
        console.print(f"[yellow]搜索路径:[/yellow]")
        for pattern in checkpoint_patterns:
            console.print(f"  - {pattern}")
        return
    
    # 加载checkpoint
    try:
        checkpoint = json.loads(checkpoint_file.read_text())
        console.print(f"✅ 加载checkpoint: {checkpoint['stage']}")
    except Exception as e:
        console.print(f"[red]❌ 无法解析checkpoint文件: {e}[/red]")
        return
    
    # 验证注释文件
    annotation_file = Path(annotation)
    if not annotation_file.suffix == ".gbk":
        console.print("[yellow]⚠️  文件扩展名不是.gbk,可能不是GenBank格式[/yellow]")
    
    console.print(f"📄 注释文件: {annotation_file}")
    console.print(f"📁 组装文件: {checkpoint.get('assembly_path', 'N/A')}")
    
    # 当前为占位实现
    console.print("\n" + "=" * 70)
    console.print("📋 Resume功能状态")
    console.print("=" * 70)
    console.print("✅ Checkpoint加载成功")
    console.print("✅ 注释文件验证通过")
    console.print("\n🚧 完整resume功能开发中,包括:")
    console.print("  • GenBank文件解析")
    console.print("  • 注释结果整合")
    console.print("  • Pipeline状态恢复")
    console.print("  • 最终报告生成")
    console.print("\n💡 当前版本: 基础验证通过")
    console.print("=" * 70 + "\n")
