from ppt2md_app.config import AppConfig
from ppt2md_app import models


def test_stage2_returns_structured_error(monkeypatch):
    monkeypatch.setattr(models, "_run_dashscope_brain", lambda filled_prompt, config: "Brain Error: 500")

    result = models.run_stage_2_brain_parallel(1, {1: "raw"}, AppConfig())

    assert result["success"] is False
    assert result["error_code"] == "Brain Error"
    assert result["error"].startswith("Brain Error")


def test_stage2_returns_sanitized_markdown(monkeypatch):
    monkeypatch.setattr(models, "_run_dashscope_brain", lambda filled_prompt, config: "正文")

    result = models.run_stage_2_brain_parallel(1, {1: "raw"}, AppConfig())

    assert result["success"] is True
    assert result["markdown"].startswith("# Slide 1")
    assert result["raw_response"] == "正文"


def test_stage2_sanitizer_removes_user_invisible_diagnostics(monkeypatch):
    monkeypatch.setattr(
        models,
        "_run_dashscope_brain",
        lambda filled_prompt, config: (
            "# Slide 1\n\n"
            "其中 $w+w^* = -1$（注：手写看似 -1/2，根据上下文逻辑修正）。\n\n"
            "> [!WARNING] 原文勘误\n"
            "> 这里是模型处理过程，不应进入正文。\n\n"
            "保留正文（普通括号）。\n"
        ),
    )

    result = models.run_stage_2_brain_parallel(1, {1: "raw"}, AppConfig())

    assert result["success"] is True
    assert result["markdown"] == "# Slide 1\n\n其中 $w+w^* = -1$。\n\n保留正文（普通括号）。\n"
    assert "原文勘误" not in result["markdown"]
    assert "手写看似" not in result["markdown"]


def test_stage2_carries_provider_usage_when_available(monkeypatch):
    monkeypatch.setattr(
        models,
        "_run_dashscope_brain",
        lambda filled_prompt, config: {
            "content": "正文",
            "usage": {"prompt_tokens": 10, "completion_tokens": 3},
            "request_id": "req-1",
            "provider_latency": 1.25,
        },
    )

    result = models.run_stage_2_brain_parallel(1, {1: "raw"}, AppConfig())

    assert result["success"] is True
    assert result["usage"] == {"prompt_tokens": 10, "completion_tokens": 3}
    assert result["request_id"] == "req-1"
    assert result["provider_latency"] == 1.25
