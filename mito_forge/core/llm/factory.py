"""
模型提供者工厂
根据配置创建合适的模型提供者实例
"""

from typing import Dict, Any, Optional, List
import os

from .provider import ModelProvider
from .unified_provider import UnifiedProvider
from .config_manager import ModelConfigManager
from ...utils.logging import get_logger

logger = get_logger(__name__)

def create_provider(config: Dict[str, Any]) -> ModelProvider:
    """
    根据配置创建模型提供者
    
    Args:
        config: 配置字典，包含模型后端和相关参数
        
    Returns:
        ModelProvider: 模型提供者实例
        
    Raises:
        ValueError: 配置无效或提供者不可用时抛出
    """
    # 优先使用新的统一提供者
    if "provider_type" in config or "profile" in config:
        return _create_unified_provider(config)
    
    # 向后兼容旧的配置格式
    backend = config.get("model_backend", "ollama").lower()
    
    # 将旧的后端名称映射到新的提供者类型
    backend_mapping = {
        "openai": "openai",
        "ollama": "ollama"
    }
    
    provider_type = backend_mapping.get(backend, backend)
    
    # 转换为统一提供者配置
    unified_config = {
        "provider_type": provider_type,
        "model": config.get("model", "gpt-4o-mini" if provider_type == "openai" else "qwen2.5:7b"),
        "api_key": config.get("api_key"),
        "api_base": config.get("api_base"),
        "timeout": config.get("timeout", 60),
        "max_retries": config.get("max_retries", 3)
    }
    
    return _create_unified_provider(unified_config)

def _create_unified_provider(config: Dict[str, Any]) -> UnifiedProvider:
    """创建统一提供者"""
    # 如果指定了配置文件名
    if "profile" in config:
        config_manager = ModelConfigManager()
        return config_manager.create_provider(config["profile"])
    
    # 直接从配置创建
    return UnifiedProvider.create_from_config(config)



def get_available_providers(config: Dict[str, Any]) -> List[str]:
    """
    获取可用的模型提供者列表
    
    Args:
        config: 配置字典
        
    Returns:
        List[str]: 可用提供者名称列表
    """
    # 使用配置管理器获取可用提供者
    try:
        config_manager = ModelConfigManager()
        profiles = config_manager.list_profiles()
        available = [profile["name"] for profile in profiles if profile["available"]]
        return available
    except Exception as e:
        logger.debug(f"Failed to get available providers from config manager: {e}")
        return []

def create_fallback_provider(config: Dict[str, Any], exclude: Optional[List[str]] = None) -> Optional[ModelProvider]:
    """
    创建备用模型提供者
    
    Args:
        config: 配置字典
        exclude: 要排除的提供者列表
        
    Returns:
        Optional[ModelProvider]: 备用提供者实例，如果没有可用的则返回 None
    """
    exclude = exclude or []
    available = get_available_providers(config)
    
    # 过滤掉排除的提供者
    available = [p for p in available if p not in exclude]
    
    if not available:
        logger.warning("No fallback providers available")
        return None
    
    # 优先级：本地模型 > 云端模型
    priority_order = ["ollama", "openai"]
    
    for provider_name in priority_order:
        if provider_name in available:
            try:
                fallback_config = config.copy()
                fallback_config["model_backend"] = provider_name
                return create_provider(fallback_config)
            except Exception as e:
                logger.warning(f"Failed to create fallback provider {provider_name}: {e}")
                continue
    
    return None

def auto_select_provider(config: Dict[str, Any]) -> ModelProvider:
    """
    自动选择最佳的模型提供者
    
    Args:
        config: 配置字典
        
    Returns:
        ModelProvider: 选中的提供者实例
        
    Raises:
        RuntimeError: 没有可用提供者时抛出
    """
    # 优先使用新的配置管理器
    try:
        config_manager = ModelConfigManager()
        return config_manager.create_provider_with_fallback()
    except Exception as e:
        logger.warning(f"Failed to use config manager: {e}")
    
    # 回退到旧的逻辑
    if "model_backend" in config:
        try:
            provider = create_provider(config)
            if provider.is_available():
                logger.info(f"Using configured provider: {config['model_backend']}")
                return provider
            else:
                logger.warning(f"Configured provider {config['model_backend']} not available, trying fallback")
        except Exception as e:
            logger.warning(f"Failed to create configured provider: {e}")
    
    # 自动选择可用的提供者
    available = get_available_providers(config)
    
    if not available:
        raise RuntimeError("No model providers are available. Please check your configuration and ensure "
                         "either OpenAI API key is set or Ollama service is running.")
    
    # 优先级：本地模型 > 云端模型
    priority_order = ["ollama", "openai"]
    
    for provider_name in priority_order:
        if provider_name in available:
            try:
                auto_config = config.copy()
                auto_config["model_backend"] = provider_name
                provider = create_provider(auto_config)
                logger.info(f"Auto-selected provider: {provider_name}")
                return provider
            except Exception as e:
                logger.warning(f"Failed to create auto-selected provider {provider_name}: {e}")
                continue
    
    raise RuntimeError("Failed to create any available provider")

def validate_provider_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证模型提供者配置
    
    Args:
        config: 配置字典
        
    Returns:
        Dict[str, Any]: 验证结果，包含错误和警告
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "available_providers": []
    }
    
    try:
        # 检查可用提供者
        available = get_available_providers(config)
        result["available_providers"] = available
        
        if not available:
            result["valid"] = False
            result["errors"].append("No model providers are available")
        
        # 检查配置的后端是否可用
        backend = config.get("model_backend")
        if backend and backend not in available:
            result["warnings"].append(f"Configured backend '{backend}' is not available")
        
        # 检查 OpenAI 配置
        if "openai" in config:
            openai_config = config["openai"]
            if not openai_config.get("api_key") and not os.getenv("OPENAI_API_KEY"):
                result["warnings"].append("OpenAI API key not configured")
        
        # 检查 Ollama 配置
        if "ollama" in config:
            ollama_config = config["ollama"]
            host = ollama_config.get("host", "http://localhost:11434")
            if "localhost" in host or "127.0.0.1" in host:
                result["warnings"].append("Ollama is configured for localhost - ensure service is running")
        
    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"Configuration validation failed: {e}")
    
    return result