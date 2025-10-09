import os
from mito_forge.core.llm.env_check import check_provider_env

def test_check_provider_env_openai_compatible(monkeypatch):
    monkeypatch.setenv("OPENAI_API_BASE", "https://inner-api.company.com/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    res = check_provider_env()
    assert res["provider"] == "openai_compatible"
    assert res["configured"] is True
    assert res["warnings"] == []

def test_check_provider_env_ollama(monkeypatch):
    monkeypatch.setenv("OPENAI_API_BASE", "http://127.0.0.1:11434/v1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)  # ollama允许无密钥
    monkeypatch.setenv("OPENAI_MODEL", "qwen2:0.5b")
    res = check_provider_env()
    assert res["provider"] == "ollama"
    assert res["configured"] is True
    assert res["warnings"] == []

def test_check_provider_env_missing(monkeypatch):
    monkeypatch.delenv("OPENAI_API_BASE", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    res = check_provider_env()
    assert res["configured"] is False
    assert len(res["warnings"]) >= 1