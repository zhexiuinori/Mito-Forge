import os
from typing import Dict, Any

def check_provider_env() -> Dict[str, Any]:
    """
    读取当前环境变量，给出LLM提供者配置状态的可读结果，不触及网络连接：
    - 根据 OPENAI_API_BASE 粗略判定为 'ollama' 或 'openai_compatible'
    - ollama 情况下允许无密钥；其他情况需要 OPENAI_API_KEY
    返回:
      {
        "provider": "ollama" | "openai_compatible",
        "api_base": str | None,
        "api_key_present": bool,
        "model": str | None,
        "configured": bool,   # 基于是否满足最小必需环境判断
        "warnings": [str, ...]
      }
    """
    api_base = os.getenv("OPENAI_API_BASE")
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL") or os.getenv("OPENAI_DEFAULT_MODEL")

    provider = "openai_compatible"
    if api_base:
        base_lower = api_base.lower()
        if "11434" in base_lower or "ollama" in base_lower:
            provider = "ollama"

    warnings = []
    api_key_present = bool(api_key)
    if provider == "ollama":
        # Ollama允许无密钥
        configured = bool(api_base) and bool(model)
        if not api_base:
            warnings.append("OPENAI_API_BASE 未设置（示例：http://127.0.0.1:11434/v1）")
        if not model:
            warnings.append("OPENAI_MODEL 未设置（示例：qwen2:0.5b）")
    else:
        # OpenAI兼容端点需要key与base与model
        configured = bool(api_base) and bool(model) and api_key_present
        if not api_base:
            warnings.append("OPENAI_API_BASE 未设置（示例：https://your-endpoint/v1）")
        if not api_key_present:
            warnings.append("OPENAI_API_KEY 未设置")
        if not model:
            warnings.append("OPENAI_MODEL 未设置（示例：gpt-4o-mini）")

    return {
        "provider": provider,
        "api_base": api_base,
        "api_key_present": api_key_present,
        "model": model,
        "configured": configured,
        "warnings": warnings,
    }