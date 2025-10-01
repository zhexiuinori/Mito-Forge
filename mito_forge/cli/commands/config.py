"""
Config 命令

配置管理
"""

import click
from rich.console import Console
import sys
from rich.table import Table
from rich.panel import Panel

from ...utils.config import Config
from ...utils.exceptions import MitoForgeError

console = Console()
from ...utils.i18n import t as __i18n_t
_t = __i18n_t
def _help(key: str) -> str:
    # 动态解析 --lang 以便帮助在渲染时按语言切换
    lang = None
    try:
        if '--lang' in sys.argv:
            # 简单解析：查找 --lang 后一个值
            args = sys.argv
            for i, a in enumerate(args):
                if a == '--lang' and i + 1 < len(args):
                    lang = args[i + 1]
                    break
        if lang is None:
            import os as _os
            lang = _os.getenv('MITO_LANG', 'zh')
    except Exception:
        lang = 'zh'
    return __i18n_t(key, lang)

from ...utils.i18n import t as _t

import os
def _t(key):
    lang = os.getenv("MITO_LANG", "zh")
    texts = {
        "zh": {
            "reset_ok": "✅ [bold green]配置已重置为默认值[/bold green]",
            "set_ok": "✅ 设置",
            "saved_to": "💾 配置已保存到",
            "cfg_title": "Mito-Forge 配置",
            "list_label": "配置项列表:",
            "desc_label": "说明",
            "not_set": "未设置",
            "file_label": "配置文件",
            "hint_set": "💡 使用 'mito-forge config --set KEY VALUE' 修改配置"
        },
        "en": {
            "reset_ok": "✅ [bold green]Reset to defaults[/bold green]",
            "set_ok": "✅ Set",
            "saved_to": "💾 Config saved to",
            "cfg_title": "Mito-Forge Config",
            "list_label": "Configuration items:",
            "desc_label": "Description",
            "not_set": "Not set",
            "file_label": "Config file",
            "hint_set": "💡 Use 'mito-forge config --set KEY VALUE' to modify"
        }
    }
    return texts.get(lang, texts["zh"]).get(key, key)

from ...utils.i18n import t as _t
@click.command()
@click.option('--show', is_flag=True, help=_help('cfg_opt_show'))
@click.option('--set', 'set_config', nargs=2, multiple=True, 
              metavar='KEY VALUE', help=_help('cfg_opt_set'))
@click.option('--reset', is_flag=True, help=_help('cfg_opt_reset'))
@click.option('--config-file', type=click.Path(), 
              help=_help('cfg_opt_config_file'))
@click.pass_context
def config(ctx, show, set_config, reset, config_file):
    """
    配置管理 / Configuration management

    管理 Mito-Forge 的配置参数
    Manage Mito-Forge configuration parameters

    示例 / Examples:
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
                console.print(_t("reset_ok"))
        
        # 设置配置项
        if set_config:
            for key, value in set_config:
                config_obj.set(key, value)
                if not quiet:
                    console.print(f"{_t('set_ok')} {key} = {value}")
        
        # 显示配置
        if show or not set_config and not reset:
            _display_config(config_obj, quiet)
        
        # 保存配置
        if set_config or reset:
            config_obj.save()
            if not quiet:
                console.print(f"\n{_t('saved_to')}: {config_obj.config_file}")
        
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
    
    console.print(f"\n  [bold blue]{_t('cfg_title')}[/bold blue]\n")
    
    config_items = [
        ("threads", _t("desc_threads")),
        ("memory", _t("desc_memory")),
        ("quality_threshold", _t("desc_quality_threshold")),
        ("assembler", _t("desc_assembler")),
        ("annotation_tool", _t("desc_annotation_tool")),
        ("output_dir", _t("desc_output_dir")),
        ("log_level", _t("desc_log_level")),
        ("temp_dir", _t("desc_temp_dir")),
    ]
    
    # 使用简单文本格式显示配置
    console.print(_t("list_label"))
    console.print("-" * 50)
    
    for key, description in config_items:
        value = config_obj.get(key, _t("not_set"))
        console.print(f"• {key}: {str(value)}")
        console.print(f"  {_t('desc_label')}: {description}")
        console.print()
    
    console.print("-" * 50)
    
    # 显示配置文件路径
    console.print(f"\n📁 {_t('file_label')}: {config_obj.config_file}")
    console.print(_t("hint_set"))