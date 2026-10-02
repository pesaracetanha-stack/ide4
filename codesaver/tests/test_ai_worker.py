# -*- coding: utf-8 -*-
# codesaver/tests/test_ai_worker.py
import pytest
from unittest.mock import patch, MagicMock
import openai
from widgets.ai_tools.worker import ApiWorker

def test_api_worker_handles_timeout_gracefully(qtbot):
    settings = {"api_key": "fake_key_123"}
    worker = ApiWorker(settings, "Hello AI", "fake_root", "fake_context")
    with patch('openai.OpenAI') as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.chat.completions.create.side_effect = openai.APITimeoutError(request=MagicMock())
        with qtbot.waitSignal(worker.error_occurred, timeout=2000) as blocker:
            worker.start()
        assert "Connection Timeout" in blocker.args[0]

def test_api_worker_successful_code_injection(qtbot):
    settings = {"api_key": "fake_key_123"}
    worker = ApiWorker(settings, "Refactor", "fake_root", "fake_context")
    fake_response = "```python\n# FILE: src/main.py\ndef hello():\n    pass\n```"
    
    with patch('openai.OpenAI') as MockClient:
        mock_message = MagicMock()
        mock_message.content = fake_response
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        mock_instance = MockClient.return_value
        mock_instance.chat.completions.create.return_value = mock_response
        
        with qtbot.waitSignal(worker.auto_inject_requested, timeout=2000) as blocker:
            worker.start()
            
        file_path, new_code = blocker.args
        assert file_path == "src/main.py"
        assert "def hello():" in new_code