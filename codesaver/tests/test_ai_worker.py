# -*- coding: utf-8 -*-
# codesaver/tests/test_ai_worker.py
import httpx
from unittest.mock import patch

from widgets.ai_tools.worker import ApiWorker, chat_completions


def _status_error(status_code):
    """Build a real httpx.HTTPStatusError for the given status code."""
    request = httpx.Request("POST", "https://example.invalid/v1/chat/completions")
    response = httpx.Response(status_code, request=request)
    return httpx.HTTPStatusError(f"HTTP {status_code}", request=request, response=response)


def test_api_worker_handles_timeout_gracefully(qtbot):
    settings = {"api_key": "fake_key_123"}
    worker = ApiWorker(settings, "Hello AI", "fake_root", "fake_context")
    with patch('widgets.ai_tools.worker.chat_completions',
               side_effect=httpx.TimeoutException("timed out")):
        with qtbot.waitSignal(worker.error_occurred, timeout=2000) as blocker:
            worker.start()
        assert "Connection Timeout" in blocker.args[0]


def test_api_worker_successful_code_injection(qtbot):
    settings = {"api_key": "fake_key_123"}
    worker = ApiWorker(settings, "Refactor", "fake_root", "fake_context")
    fake_response = "```python\n# FILE: src/main.py\ndef hello():\n    pass\n```"

    with patch('widgets.ai_tools.worker.chat_completions',
               return_value=fake_response):
        with qtbot.waitSignal(worker.auto_inject_requested, timeout=2000) as blocker:
            worker.start()

        file_path, new_code = blocker.args
        assert file_path == "src/main.py"
        assert "def hello():" in new_code


def test_api_worker_maps_auth_error(qtbot):
    settings = {"api_key": "fake_key_123"}
    worker = ApiWorker(settings, "Hello AI", "fake_root", "fake_context")
    with patch('widgets.ai_tools.worker.chat_completions',
               side_effect=_status_error(401)):
        with qtbot.waitSignal(worker.error_occurred, timeout=2000) as blocker:
            worker.start()
        assert "Authentication Error" in blocker.args[0]


def test_api_worker_maps_rate_limit(qtbot):
    settings = {"api_key": "fake_key_123"}
    worker = ApiWorker(settings, "Hello AI", "fake_root", "fake_context")
    with patch('widgets.ai_tools.worker.chat_completions',
               side_effect=_status_error(429)):
        with qtbot.waitSignal(worker.error_occurred, timeout=2000) as blocker:
            worker.start()
        assert "Rate Limit Exceeded" in blocker.args[0]


def test_chat_completions_retries_on_429_then_succeeds(monkeypatch):
    """Unit test for the retry loop: 429 then 200 must yield content."""
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, json={"error": "rate limited"})
        return httpx.Response(200, json={
            "choices": [{"message": {"role": "assistant", "content": "hello"}}]
        })

    transport = httpx.MockTransport(handler)
    # Bypass the backoff sleep to keep the test fast.
    monkeypatch.setattr("widgets.ai_tools.worker.time.sleep", lambda s: None)
    with patch("widgets.ai_tools.worker.httpx.HTTPTransport", return_value=transport):
        content = chat_completions(
            "https://example.invalid/v1", "key", "m", [{"role": "user", "content": "hi"}]
        )
    assert calls["n"] == 2, "expected exactly one retry after 429"
    assert content == "hello"


def test_chat_completions_normalizes_base_url():
    """Trailing slash must not produce a double slash in the endpoint URL."""
    captured = {}

    def handler(request):
        captured["url"] = str(request.url)
        return httpx.Response(200, json={
            "choices": [{"message": {"content": "ok"}}]
        })

    transport = httpx.MockTransport(handler)
    with patch("widgets.ai_tools.worker.httpx.HTTPTransport", return_value=transport):
        content = chat_completions(
            "https://example.invalid/v1/", "key", "m", [{"role": "user", "content": "hi"}]
        )
    assert captured["url"] == "https://example.invalid/v1/chat/completions"
    assert content == "ok"
