"""
Doctor 命令

系统健康检查和诊断
"""

import click
import sys
import shutil
import subprocess
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ...utils.config import Config
from ...utils.exceptions import MitoForgeError

console = Console()

from ...utils.i18n import t as _t

import os
def _t(key):
    lang = os.getenv("MITO_LANG", "zh")
    texts = {
        "zh": {
            "title": "🏥 Mito-Forge 系统诊断",
            "sys_check": "🖥️  [bold]系统环境检查[/bold]",
            "deps_check": "\n🐍 [bold]Python依赖检查[/bold]",
            "tools_check": "\n🧬 [bold]生物信息学工具检查[/bold]",
            "issues_found": "\n发现的问题:",
            "summary_label": "📊 诊断摘要",
            "all_passed": "\n🎉 [bold green]所有检查都通过了！[/bold green]",
            "ready": "Mito-Forge已准备就绪。",
            "error_in_diag": "诊断过程中出现错误"
        },
        "en": {
            "title": "🏥 Mito-Forge System Doctor",
            "sys_check": "🖥️  [bold]System environment check[/bold]",
            "deps_check": "\n🐍 [bold]Python dependencies check[/bold]",
            "tools_check": "\n🧬 [bold]Bioinformatics tools check[/bold]",
            "issues_found": "\nIssues found:",
            "summary_label": "📊 Summary",
            "all_passed": "\n🎉 [bold green]All checks passed![/bold green]",
            "ready": "Mito-Forge is ready.",
            "error_in_diag": "Error during diagnostics"
        }
    }
    return texts.get(lang, texts["zh"]).get(key, key)

@click.command()
@click.option('--check-tools', is_flag=True, help='检查生物信息学工具')
@click.option('--check-system', is_flag=True, help='检查系统环境')
@click.option('--check-dependencies', is_flag=True, help='检查Python依赖')
@click.option('--fix-issues', is_flag=True, help='尝试自动修复问题')
@click.pass_context
def doctor(ctx, check_tools, check_system, check_dependencies, fix_issues):
    """
    系统健康检查和诊断
    
    检查Mito-Forge运行环境，诊断潜在问题
    
    示例:
        mito-forge doctor
        mito-forge doctor --check-tools
        mito-forge doctor --fix-issues
    """
    verbose = ctx.obj.get('verbose', False) if ctx.obj else False
    quiet = ctx.obj.get('quiet', False) if ctx.obj else False
    
    if not quiet:
        console.print(f"\n[bold blue]{_t('title')}[/bold blue]\n")
    
    issues = []
    
    # 如果没有指定具体检查，则执行全部检查
    if not any([check_tools, check_system, check_dependencies]):
        check_tools = check_system = check_dependencies = True
    
    try:
        # 系统环境检查
        if check_system:
            issues.extend(_check_system_environment(verbose, quiet))
        
        # Python依赖检查
        if check_dependencies:
            issues.extend(_check_python_dependencies(verbose, quiet))
        
        # 生物信息学工具检查
        if check_tools:
            issues.extend(_check_bioinformatics_tools(verbose, quiet))
        
        # 显示总结
        if not quiet:
            _display_summary(issues, fix_issues)
        
        # 尝试修复问题
        if fix_issues and issues:
            _fix_issues(issues, verbose, quiet)
        
        return 0 if not issues else 1
        
    except Exception as e:
        console.print(f"\n💥 [bold red]{_t('error_in_diag')}:[/bold red] {e}")
        if verbose:
            console.print_exception()
        return 1

def _check_system_environment(verbose, quiet):
    """检查系统环境"""
    issues = []
    
    if not quiet:
        console.print(_t("sys_check"))
    
    # Python版本检查
    python_version = sys.version_info
    if python_version < (3, 8):
        issues.append({
            'type': 'error',
            'category': 'system',
            'message': f'Python版本过低: {python_version.major}.{python_version.minor}',
            'suggestion': '需要Python 3.8或更高版本'
        })
    elif not quiet:
        console.print(f"  ✅ {'Python版本' if os.getenv('MITO_LANG','zh')!='en' else 'Python version'}: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 内存检查
    try:
        import psutil
        memory = psutil.virtual_memory()
        if memory.total < 4 * 1024**3:  # 4GB
            issues.append({
                'type': 'warning',
                'category': 'system',
                'message': f'系统内存较低: {memory.total / 1024**3:.1f}GB',
                'suggestion': '推荐至少4GB内存用于大数据集处理'
            })
        elif not quiet:
            console.print(f"  ✅ {'系统内存' if os.getenv('MITO_LANG','zh')!='en' else 'System memory'}: {memory.total / 1024**3:.1f}GB")
    except ImportError:
        if not quiet:
            console.print("  ⚠️  无法检查内存信息 (缺少psutil)")
    
    # 磁盘空间检查
    try:
        disk_usage = shutil.disk_usage('.')
        free_gb = disk_usage.free / 1024**3
        if free_gb < 10:  # 10GB
            issues.append({
                'type': 'warning',
                'category': 'system',
                'message': f'磁盘空间不足: {free_gb:.1f}GB',
                'suggestion': '推荐至少10GB可用空间'
            })
        elif not quiet:
            console.print(f"  ✅ {'可用磁盘空间' if os.getenv('MITO_LANG','zh')!='en' else 'Free disk space'}: {free_gb:.1f}GB")
    except Exception:
        if not quiet:
            console.print("  ⚠️  无法检查磁盘空间")
    
    return issues

def _check_python_dependencies(verbose, quiet):
    """检查Python依赖"""
    issues = []
    
    if not quiet:
        console.print(_t("deps_check"))
    
    required_packages = [
        'click', 'rich', 'biopython', 'numpy', 'pandas'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            if not quiet:
                console.print(f"  ✅ {package}")
        except ImportError:
            issues.append({
                'type': 'error',
                'category': 'dependencies',
                'message': f'缺少Python包: {package}',
                'suggestion': f'运行: pip install {package}'
            })
            if not quiet:
                console.print(f"  ❌ {package}")
    
    return issues

def _check_bioinformatics_tools(verbose, quiet):
    """检查生物信息学工具"""
    issues = []
    
    if not quiet:
        console.print(_t("tools_check"))
    
    tools = {
        'fastqc': 'FastQC',
        'spades.py': 'SPAdes',
        'blastn': 'BLAST+',
        'muscle': 'MUSCLE',
        'iqtree': 'IQ-TREE'
    }
    
    for cmd, name in tools.items():
        if shutil.which(cmd):
            if not quiet:
                console.print(f"  ✅ {name}")
        else:
            issues.append({
                'type': 'warning',
                'category': 'tools',
                'message': f'未找到工具: {name} ({cmd})',
                'suggestion': f'请安装{name}或确保其在PATH中'
            })
            if not quiet:
                console.print(f"  ❌ {name}")
    
    return issues

def _display_summary(issues, fix_issues):
    """显示诊断摘要"""
    if not issues:
        console.print(_t("all_passed"))
        console.print(_t("ready"))
        return
    
    # 统计问题
    errors = [i for i in issues if i['type'] == 'error']
    warnings = [i for i in issues if i['type'] == 'warning']
    
    console.print(_t("issues_found"))
    console.print("=" * 80)
    
    for i, issue in enumerate(issues, 1):
        icon = "❌" if issue['type'] == 'error' else "⚠️"
        console.print(f"{i}. {icon} {issue['type'].upper()}")
        console.print(f"   {'问题' if os.getenv('MITO_LANG','zh')!='en' else 'Issue'}: {issue['message']}")
        console.print(f"   {'建议' if os.getenv('MITO_LANG','zh')!='en' else 'Suggestion'}: {issue['suggestion']}")
        console.print()
    
    console.print("=" * 80)
    
    # 显示摘要
    summary = f"{'发现' if os.getenv('MITO_LANG','zh')!='en' else 'Found'} {len(errors)} {'个错误和' if os.getenv('MITO_LANG','zh')!='en' else 'errors and'} {len(warnings)} {'个警告' if os.getenv('MITO_LANG','zh')!='en' else 'warnings'}"
    if fix_issues:
        summary += "\n正在尝试自动修复..."
    
    console.print(f"\n{_t('summary_label')}: {summary}")

def _fix_issues(issues, verbose, quiet):
    """尝试修复问题"""
    if not quiet:
        console.print("\n🔧 [bold]尝试自动修复[/bold]")
    
    fixed = 0
    
    for issue in issues:
        if issue['category'] == 'dependencies':
            # 尝试安装缺少的Python包
            package = issue['message'].split(': ')[1]
            try:
                if not quiet:
                    console.print(f"  📦 安装 {package}...")
                subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                             check=True, capture_output=True)
                if not quiet:
                    console.print(f"  ✅ {package} 安装成功")
                fixed += 1
            except subprocess.CalledProcessError:
                if not quiet:
                    console.print(f"  ❌ {package} 安装失败")
    
    if not quiet:
        console.print(f"\n修复了 {fixed} 个问题")
        if fixed > 0:
            console.print("建议重新运行诊断以验证修复结果")