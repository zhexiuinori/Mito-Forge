#!/usr/bin/env python3
"""
测试统一模型提供者的示例脚本
演示如何使用新的模型配置系统
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mito_forge.core.llm.unified_provider import UnifiedProvider
from mito_forge.core.llm.config_manager import ModelConfigManager
from mito_forge.utils.logging import get_logger

logger = get_logger(__name__)

def test_unified_provider():
    """测试统一提供者的基本功能"""
    print("🧪 测试统一模型提供者")
    print("=" * 50)
    
    # 1. 显示所有预设配置
    print("\n📋 可用的预设配置:")
    presets = UnifiedProvider.get_preset_configs()
    for name, config in presets.items():
        print(f"  {name}: {config['default_model']} ({config['api_base']})")
    
    # 2. 测试 Ollama（如果可用）
    print("\n🤖 测试 Ollama 提供者:")
    try:
        ollama_provider = UnifiedProvider(
            provider_type="ollama",
            model="qwen2.5:7b"
        )
        
        if ollama_provider.is_available():
            print("  ✅ Ollama 可用")
            try:
                response = ollama_provider.generate("你好，请简单介绍一下自己", max_tokens=100)
                print(f"  📝 测试响应: {response[:100]}...")
            except Exception as e:
                print(f"  ❌ 生成失败: {e}")
        else:
            print("  ❌ Ollama 不可用（可能服务未启动）")
    except Exception as e:
        print(f"  ❌ Ollama 提供者创建失败: {e}")
    
    # 3. 测试 OpenAI（如果有 API 密钥）
    print("\n🌐 测试 OpenAI 提供者:")
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            openai_provider = UnifiedProvider(
                provider_type="openai",
                model="gpt-4o-mini",
                api_key=openai_key
            )
            
            if openai_provider.is_available():
                print("  ✅ OpenAI 可用")
                try:
                    response = openai_provider.generate("Hello, please introduce yourself briefly", max_tokens=50)
                    print(f"  📝 测试响应: {response[:100]}...")
                except Exception as e:
                    print(f"  ❌ 生成失败: {e}")
            else:
                print("  ❌ OpenAI 不可用")
        except Exception as e:
            print(f"  ❌ OpenAI 提供者创建失败: {e}")
    else:
        print("  ⚠️  未设置 OPENAI_API_KEY 环境变量")
    
    # 4. 测试自定义配置
    print("\n⚙️  测试自定义配置:")
    try:
        custom_config = {
            "provider_type": "openai_compatible",
            "model": "gpt-3.5-turbo",
            "api_base": "http://localhost:8000/v1",
            "api_key": "test-key"
        }
        
        custom_provider = UnifiedProvider.create_from_config(custom_config)
        print(f"  ✅ 自定义提供者创建成功: {custom_provider.get_model_info()}")
        
        # 注意：这个测试可能会失败，因为没有实际的服务器
        if custom_provider.is_available():
            print("  ✅ 自定义服务可用")
        else:
            print("  ❌ 自定义服务不可用（预期结果，因为没有实际服务器）")
            
    except Exception as e:
        print(f"  ❌ 自定义提供者创建失败: {e}")

def test_config_manager():
    """测试配置管理器"""
    print("\n🔧 测试配置管理器")
    print("=" * 50)
    
    try:
        config_manager = ModelConfigManager()
        
        # 1. 显示配置文件位置
        print(f"\n📁 配置目录: {config_manager.config_dir}")
        print(f"  主配置文件: {config_manager.config_file}")
        print(f"  配置文件: {config_manager.profiles_file}")
        
        # 2. 列出所有配置文件
        print("\n📋 当前配置文件:")
        profiles = config_manager.list_profiles()
        for profile in profiles:
            status = "✅" if profile["available"] else "❌"
            print(f"  {status} {profile['name']}: {profile['description']}")
        
        # 3. 尝试创建提供者
        print(f"\n🚀 尝试创建默认提供者:")
        try:
            provider = config_manager.create_provider_with_fallback()
            info = provider.get_model_info()
            print(f"  ✅ 成功创建: {info['provider_type']} - {info['model']}")
            
            # 测试生成
            try:
                response = provider.generate("测试", max_tokens=20)
                print(f"  📝 测试生成: {response[:50]}...")
            except Exception as e:
                print(f"  ❌ 生成测试失败: {e}")
                
        except Exception as e:
            print(f"  ❌ 无法创建提供者: {e}")
            print("  💡 提示: 请设置 API 密钥或启动 Ollama 服务")
        
    except Exception as e:
        print(f"❌ 配置管理器测试失败: {e}")

def test_json_generation():
    """测试 JSON 生成功能"""
    print("\n📄 测试 JSON 生成")
    print("=" * 50)
    
    try:
        config_manager = ModelConfigManager()
        provider = config_manager.create_provider_with_fallback()
        
        # 测试 JSON 生成
        prompt = """
        请生成一个包含以下信息的 JSON 对象：
        - name: 一个随机的人名
        - age: 20-60之间的随机年龄
        - city: 一个城市名
        - hobbies: 包含2-3个爱好的数组
        """
        
        print("🔄 生成 JSON 响应...")
        json_response = provider.generate_json(prompt, max_tokens=200)
        
        print("📝 生成的 JSON:")
        import json
        print(json.dumps(json_response, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ JSON 生成测试失败: {e}")

def main():
    """主测试函数"""
    print("🧬 Mito-Forge 统一模型提供者测试")
    print("=" * 60)
    
    # 设置日志级别
    os.environ.setdefault("MITO_FORGE_LOG_LEVEL", "INFO")
    
    try:
        # 运行各项测试
        test_unified_provider()
        test_config_manager()
        test_json_generation()
        
        print("\n" + "=" * 60)
        print("✅ 测试完成！")
        print("\n💡 使用提示:")
        print("1. 运行 'python -m mito_forge.cli.main model list' 查看所有配置")
        print("2. 运行 'python -m mito_forge.cli.main model doctor' 诊断问题")
        print("3. 运行 'python -m mito_forge.cli.main model presets' 查看预设配置")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()