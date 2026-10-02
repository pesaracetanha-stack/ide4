# -*- coding: utf-8 -*-
# codesaver/tests/test_git_manager.py
import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtCore import QObject
from core.git_manager import GitManager, GitStatusWorker

class FakeMainWindow(QObject):
    pass

def test_git_worker_handles_missing_git(qtbot):
    worker = GitStatusWorker("dummy_path")
    with patch('subprocess.run', side_effect=FileNotFoundError("No git")):
        with qtbot.waitSignal(worker.error_occurred, timeout=2000) as blocker:
            worker.start()
        assert blocker.args[0] == "GIT_NOT_FOUND"

def test_git_manager_commit_fails_gracefully():
    mw = FakeMainWindow()
    manager = GitManager(mw)
    with patch('subprocess.run', side_effect=FileNotFoundError("No git")):
        success, message = manager.git_commit_all("dummy_path", "Init")
        assert success is False
        assert "Git is not installed" in message

def test_git_manager_survives_corrupted_output(qtbot):
    worker = GitStatusWorker("dummy_path")
    with patch('subprocess.run') as mock_run:
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = "?? \x00corrupt_file\n M  normal.py\n\x01\x02\n"
        mock_run.return_value = mock_res
        
        with qtbot.waitSignal(worker.status_ready, timeout=2000) as blocker:
            worker.start()
        
        states = blocker.args[0]
        assert any("normal.py" in k for k in states.keys())