import os
from mito_forge.utils.report_utils import render_template_summary, summarize_on_llm_fail

def test_render_template_summary_basic():
    ctx = {
        "task_name": "示例任务",
        "inputs": {"reads": "reads.fastq"},
        "outputs": {},
        "metrics": {}
    }
    s = render_template_summary(ctx)
    assert "【模板汇总】" in s
    assert "任务: 示例任务" in s
    assert "输入要点" in s

def test_summarize_on_llm_fail_enabled(monkeypatch):
    monkeypatch.setenv("MITO_TEMPLATE_ON_LLM_FAIL", "1")
    ctx = {"task_name": "示例任务", "inputs": {}, "outputs": {}, "metrics": {}}
    out = summarize_on_llm_fail("[LLM不可用]", ctx)
    assert "[LLM不可用]" in out
    assert "【模板汇总】" in out

def test_summarize_on_llm_fail_disabled(monkeypatch):
    # 默认关闭
    monkeypatch.delenv("MITO_TEMPLATE_ON_LLM_FAIL", raising=False)
    ctx = {"task_name": "示例任务", "inputs": {}, "outputs": {}, "metrics": {}}
    out = summarize_on_llm_fail("[LLM错误]", ctx)
    assert out == "[LLM错误]"