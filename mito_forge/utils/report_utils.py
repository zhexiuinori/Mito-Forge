import os
from typing import Dict, Any

def render_template_summary(context: Dict[str, Any]) -> str:
    """
    生成一个简短的中文模板汇总，用于在生成模型不可用或出错时，给用户可读的摘要。
    不依赖 Agent 内部逻辑，仅使用外部上下文信息。
    """
    task = context.get("task_name") or context.get("name") or "未命名任务"
    inputs = context.get("inputs") or {}
    outputs = context.get("outputs") or {}
    metrics = context.get("metrics") or {}

    lines = []
    lines.append("【模板汇总】")
    lines.append(f"- 任务: {task}")
    if inputs:
        lines.append(f"- 输入要点: {', '.join(k for k in inputs.keys())}")
    else:
        lines.append("- 输入要点: 无")
    if outputs:
        lines.append(f"- 产出概览: {', '.join(k for k in outputs.keys())}")
    else:
        lines.append("- 产出概览: 无")
    if metrics:
        lines.append(f"- 指标: {', '.join(f'{k}={v}' for k, v in metrics.items())}")
    else:
        lines.append("- 指标: 无")
    lines.append("- 说明: 由于生成模型不可用或发生错误，以上为基于上下文的简要汇总。")

    return "\n".join(lines)

def summarize_on_llm_fail(provider_error: str, context: Dict[str, Any]) -> str:
    """
    在LLM失败时的外层汇总逻辑：
    - 若环境变量 MITO_TEMPLATE_ON_LLM_FAIL 开启(‘1’, ‘true’, ‘True’)，则返回 错误信息 + 模板汇总
    - 否则仅返回错误信息（保持默认行为，不改Agent）
    """
    flag = os.getenv("MITO_TEMPLATE_ON_LLM_FAIL", "").strip().lower()
    enabled = flag in {"1", "true", "yes", "on"}
    if enabled:
        tmpl = render_template_summary(context)
        return f"{provider_error}\n{tmpl}"
    return provider_error