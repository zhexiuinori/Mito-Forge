"""
模型配置管理命令
提供用户友好的模型配置和切换功能
"""

import click
import json
import yaml
import os
from pathlib import Path
from typing import Dict, Any

from ...core.llm.config_manager import ModelConfigManager
from ...core.llm.unified_provider import UnifiedProvider
from ...utils.logging import get_logger

logger = get_logger(__name__)

from ...utils.i18n import t as _t

@click.group()
def model():
    """模型配置管理 / Model configuration management"""
    pass

@model.command()
def list():
    """列出所有可用的模型配置"""
    config_manager = ModelConfigManager()
    profiles = config_manager.list_profiles()
    
    if not profiles:
        click.echo(_t("no_profiles"))
        return
    
    click.echo(_t("available_profiles"))
    click.echo("-" * 80)
    
    for profile in profiles:
        status = _t("available") if profile["available"] else _t("unavailable")
        click.echo(f"{_t('name')}: {profile['name']}")
        click.echo(f"{_t('description')}: {profile['description']}")
        click.echo(f"{_t('provider')}: {profile['provider_type']}")
        click.echo(f"{_t('model')}: {profile['model']}")
        click.echo(f"{_t('status')}: {status}")
        click.echo("-" * 40)

@model.command()
@click.argument('name')
def show(name: str):
    """显示指定配置的详细信息"""
    config_manager = ModelConfigManager()
    profile = config_manager.get_profile(name)
    
    if not profile:
        click.echo(f"{_t('profile_not_exists')} '{name}'", err=True)
        return
    
    click.echo(f"{_t('config_label')}: {name}")
    click.echo("-" * 40)
    
    for key, value in profile.items():
        if key == "api_key" and value:
            # 隐藏 API 密钥
            value = "*" * 8 + value[-4:] if len(value) > 4 else "*" * len(value)
        click.echo(f"{key}: {value}")

@model.command()
@click.argument('name')
def test(name: str):
    """测试指定的模型配置"""
    config_manager = ModelConfigManager()
    
    click.echo(f"{_t('testing_config')}: {name}")
    
    with click.progressbar(length=100, label=_t("testing")) as bar:
        bar.update(50)
        result = config_manager.test_profile(name)
        bar.update(100)
    
    if result["success"]:
        click.echo(_t("test_success"))
        if "test_response" in result:
            click.echo(("测试响应: " if os.getenv("MITO_LANG","zh")!="en" else "Test response: ") + f"{result['test_response']}")
    else:
        click.echo(_t("test_failed"))
        click.echo(f"{_t('error')}: {result['error']}")

@model.command()
@click.argument('name')
def use(name: str):
    """设置默认模型配置"""
    config_manager = ModelConfigManager()
    
    try:
        config_manager.set_default_profile(name)
        click.echo(f"{_t('set_default_ok')}: {name}")
    except ValueError as e:
        click.echo(f"❌ {_t('error')}: {e}", err=True)

@model.command()
@click.argument('name')
@click.option('--provider-type', required=True, help='提供者类型 (openai, ollama, zhipu, etc.)')
@click.option('--model', required=True, help='模型名称')
@click.option('--api-key', help='API 密钥')
@click.option('--api-base', help='API 基础 URL')
@click.option('--description', help='配置描述')
def add(name: str, provider_type: str, model: str, api_key: str, api_base: str, description: str):
    """添加新的模型配置"""
    config_manager = ModelConfigManager()
    
    # 构建配置
    profile_config = {
        "provider_type": provider_type,
        "model": model,
        "description": description or f"{provider_type} {model}"
    }
    
    if api_key:
        profile_config["api_key"] = api_key
    
    if api_base:
        profile_config["api_base"] = api_base
    
    try:
        config_manager.add_profile(name, profile_config)
        click.echo(f"{_t('add_ok')}: {name}")
        
        # 询问是否测试
        if click.confirm(_t("confirm_test_new")):
            result = config_manager.test_profile(name)
            if result["success"]:
                click.echo(_t("update_test_success"))
            else:
                click.echo(f"{_t('update_test_failed')}: {result['error']}")
                
    except Exception as e:
        click.echo(f"{_t('add_fail')}: {e}", err=True)

@model.command()
@click.argument('name')
@click.option('--provider-type', help='提供者类型')
@click.option('--model', help='模型名称')
@click.option('--api-key', help='API 密钥')
@click.option('--api-base', help='API 基础 URL')
@click.option('--description', help='配置描述')
def update(name: str, provider_type: str, model: str, api_key: str, api_base: str, description: str):
    """更新现有的模型配置"""
    config_manager = ModelConfigManager()
    
    # 构建更新配置
    updates = {}
    
    if provider_type:
        updates["provider_type"] = provider_type
    if model:
        updates["model"] = model
    if api_key:
        updates["api_key"] = api_key
    if api_base:
        updates["api_base"] = api_base
    if description:
        updates["description"] = description
    
    if not updates:
        click.echo(_t("update_no_fields"), err=True)
        return
    
    try:
        config_manager.update_profile(name, updates)
        click.echo(f"{_t('update_ok')}: {name}")
        
        # 询问是否测试
        if click.confirm(("是否测试更新后的配置?" if os.getenv("MITO_LANG","zh")!="en" else "Test the updated profile?")):
            result = config_manager.test_profile(name)
            if result["success"]:
                click.echo(_t("update_test_success"))
            else:
                click.echo(f"{_t('update_test_failed')}: {result['error']}")
                
    except Exception as e:
        click.echo("❌ " + (("更新配置失败: " if os.getenv("MITO_LANG","zh")!="en" else "Update profile failed: ")) + f"{e}", err=True)

@model.command()
@click.argument('name')
@click.confirmation_option(prompt='确定要删除这个配置吗?')
def remove(name: str):
    """删除模型配置"""
    config_manager = ModelConfigManager()
    
    try:
        config_manager.remove_profile(name)
        click.echo(f"{_t('remove_ok')}: {name}")
    except Exception as e:
        click.echo("❌ " + (("删除配置失败: " if os.getenv("MITO_LANG","zh")!="en" else "Remove profile failed: ")) + f"{e}", err=True)

@model.command()
def presets():
    """显示所有预设配置"""
    presets = UnifiedProvider.get_preset_configs()
    
    click.echo(_t("presets_available"))
    click.echo("-" * 60)
    
    for name, config in presets.items():
        click.echo(f"{_t('name')}: {name}")
        click.echo(f"{_t('api_base')}: {config['api_base']}")
        click.echo(f"{_t('default_model')}: {config['default_model']}")
        click.echo(f"{_t('api_format')}: {config['api_format']}")
        click.echo("-" * 30)

@model.command()
@click.argument('preset_name')
@click.argument('profile_name')
@click.option('--api-key', help='API 密钥')
@click.option('--model', help='模型名称 (覆盖默认)')
def create_from_preset(preset_name: str, profile_name: str, api_key: str, model: str):
    """从预设创建新的配置"""
    presets = UnifiedProvider.get_preset_configs()
    
    if preset_name not in presets:
        click.echo((f"预设 '{preset_name}' 不存在" if os.getenv("MITO_LANG","zh")!="en" else f"Preset '{preset_name}' not found"), err=True)
        click.echo(( "可用预设: " if os.getenv("MITO_LANG","zh")!="en" else "Available presets: ") + f"{', '.join(presets.keys())}")
        return
    
    preset = presets[preset_name]
    config_manager = ModelConfigManager()
    
    # 构建配置
    profile_config = {
        "provider_type": preset_name,
        "model": model or preset["default_model"],
        "api_base": preset["api_base"],
        "description": f"基于 {preset_name} 预设创建"
    }
    
    if api_key:
        profile_config["api_key"] = api_key
    elif preset_name != "ollama":  # Ollama 不需要 API 密钥
        env_var = f"{preset_name.upper()}_API_KEY"
        profile_config["api_key"] = f"${{{env_var}}}"
    
    try:
        config_manager.add_profile(profile_name, profile_config)
        click.echo("✅ " + (f"已从预设 '{preset_name}' 创建配置: " if os.getenv("MITO_LANG","zh")!="en" else f"Created profile from preset '{preset_name}': ") + f"{profile_name}")
        
        if preset_name != "ollama" and not api_key:
            click.echo(("💡 提示: 请设置环境变量 " if os.getenv("MITO_LANG","zh")!="en" else "💡 Tip: Set environment variable ") + f"{env_var}" + ( " 或使用 'mito-forge model update " if os.getenv("MITO_LANG","zh")!="en" else " or use 'mito-forge model update ") + f"{profile_name}" + ( " --api-key YOUR_KEY' 设置 API 密钥" if os.getenv("MITO_LANG","zh")!="en" else " --api-key YOUR_KEY' to set the API key"))
        
    except Exception as e:
        click.echo("❌ " + (("创建配置失败: " if os.getenv("MITO_LANG","zh")!="en" else "Create profile failed: ")) + f"{e}", err=True)

@model.command()
@click.argument('file_path', type=click.Path())
def export(file_path: str):
    """导出配置到文件"""
    config_manager = ModelConfigManager()
    
    try:
        config_manager.export_config(Path(file_path))
        click.echo(("✅ 配置已导出到: " if os.getenv("MITO_LANG","zh")!="en" else "✅ Config exported to: ") + f"{file_path}")
    except Exception as e:
        click.echo("❌ " + (("导出失败: " if os.getenv("MITO_LANG","zh")!="en" else "Export failed: ")) + f"{e}", err=True)

@model.command()
@click.argument('file_path', type=click.Path(exists=True))
def import_config(file_path: str):
    """从文件导入配置"""
    config_manager = ModelConfigManager()
    
    try:
        config_manager.import_config(Path(file_path))
        click.echo(("✅ 配置已从 " if os.getenv("MITO_LANG","zh")!="en" else "✅ Config imported from ") + f"{file_path}")
    except Exception as e:
        click.echo("❌ " + (("导入失败: " if os.getenv("MITO_LANG","zh")!="en" else "Import failed: ")) + f"{e}", err=True)

@model.command()
def current():
    """显示当前默认配置"""
    config_manager = ModelConfigManager()
    default_profile = config_manager.config.get("default_profile", "未设置")
    
    click.echo(( "当前默认配置: " if os.getenv("MITO_LANG","zh")!="en" else "Current default profile: ") + f"{default_profile}")
    
    if default_profile != "未设置":
        profile = config_manager.get_profile(default_profile)
        if profile:
            click.echo("\n" + ("配置详情:" if os.getenv("MITO_LANG","zh")!="en" else "Profile details:"))
            click.echo("-" * 30)
            for key, value in profile.items():
                if key == "api_key" and value:
                    value = "*" * 8 + value[-4:] if len(value) > 4 else "*" * len(value)
                click.echo(f"{key}: {value}")

@model.command()
def doctor():
    """诊断模型配置问题"""
    config_manager = ModelConfigManager()
    
    click.echo("🔍 " + ("诊断模型配置..." if os.getenv("MITO_LANG","zh")!="en" else "Diagnosing model configuration..."))
    click.echo("-" * 50)
    
    # 检查配置文件
    click.echo("📁 " + ("配置文件:" if os.getenv("MITO_LANG","zh")!="en" else "Config files:"))
    click.echo(("  配置目录: " if os.getenv("MITO_LANG","zh")!="en" else "  Config dir: ") + f"{config_manager.config_dir}")
    click.echo(("  主配置: " if os.getenv("MITO_LANG","zh")!="en" else "  Main config: ") + ("✅ 存在" if config_manager.config_file.exists() else "❌ 不存在"))
    click.echo(("  配置文件: " if os.getenv("MITO_LANG","zh")!="en" else "  Profiles file: ") + ("✅ 存在" if config_manager.profiles_file.exists() else "❌ 不存在"))
    
    # 检查环境变量
    click.echo("\n🔑 " + ("环境变量:" if os.getenv("MITO_LANG","zh")!="en" else "Environment variables:"))
    env_vars = ["OPENAI_API_KEY", "ZHIPU_API_KEY", "MOONSHOT_API_KEY", "DEEPSEEK_API_KEY"]
    for var in env_vars:
        value = os.getenv(var)
        status = ("✅ 已设置" if os.getenv("MITO_LANG","zh")!="en" else "✅ Set") if value else ("❌ 未设置" if os.getenv("MITO_LANG","zh")!="en" else "❌ Not set")
        click.echo(f"  {var}: {status}")
    
    # 检查配置文件可用性
    click.echo("\n🚀 " + ("配置文件状态:" if os.getenv("MITO_LANG","zh")!="en" else "Profiles status:"))
    profiles = config_manager.list_profiles()
    
    available_count = 0
    for profile in profiles:
        status = ("✅ 可用" if os.getenv("MITO_LANG","zh")!="en" else "✅ Available") if profile["available"] else ("❌ 不可用" if os.getenv("MITO_LANG","zh")!="en" else "❌ Unavailable")
        click.echo(f"  {profile['name']}: {status}")
        if profile["available"]:
            available_count += 1
    
    # 总结
    click.echo("\n📊 " + ("总结:" if os.getenv("MITO_LANG","zh")!="en" else "Summary:"))
    click.echo(("  总配置数: " if os.getenv("MITO_LANG","zh")!="en" else "  Total profiles: ") + f"{len(profiles)}")
    click.echo(("  可用配置: " if os.getenv("MITO_LANG","zh")!="en" else "  Available profiles: ") + f"{available_count}")
    click.echo(("  默认配置: " if os.getenv("MITO_LANG","zh")!="en" else "  Default profile: ") + f"{config_manager.config.get('default_profile', '未设置')}")
    
    if available_count == 0:
        click.echo("\n" + ("⚠️  警告: 没有可用的模型配置!" if os.getenv("MITO_LANG","zh")!="en" else "⚠️  Warning: No available model profiles!"))
        click.echo("建议:" if os.getenv("MITO_LANG","zh")!="en" else "Suggestions:")
        click.echo("1. 设置相应的 API 密钥环境变量" if os.getenv("MITO_LANG","zh")!="en" else "1. Set the corresponding API key environment variables")
        click.echo("2. 或启动本地 Ollama 服务" if os.getenv("MITO_LANG","zh")!="en" else "2. Or start local Ollama service")
        click.echo("3. 使用 'mito-forge model add' 添加自定义配置" if os.getenv("MITO_LANG","zh")!="en" else "3. Use 'mito-forge model add' to add a custom profile")
    else:
        click.echo(("\n✅ 系统正常，有 " if os.getenv("MITO_LANG","zh")!="en" else "\n✅ System OK, available profiles ") + f"{available_count}" + ("" if os.getenv("MITO_LANG","zh")=="en" else " 个可用配置"))

if __name__ == "__main__":
    model()