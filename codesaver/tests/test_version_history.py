# -*- coding: utf-8 -*-
# codesaver/tests/test_version_history.py
import pytest
import sqlite3
from unittest.mock import patch
from core.version_history import VersionHistoryManager

def test_version_history_saves_and_retrieves_code(tmp_path):
    manager = VersionHistoryManager()
    manager.set_project_root(str(tmp_path))
    
    test_file_path = str(tmp_path / "main.py")
    test_code = "def IDE(): pass"
    
    manager.save_version(test_file_path, test_code)
    versions = manager.get_versions(test_file_path)
    
    assert len(versions) == 1
    loaded_code = manager.load_version(test_file_path, versions[0])
    assert loaded_code == test_code

def test_version_history_survives_locked_database(tmp_path):
    manager = VersionHistoryManager()
    manager.set_project_root(str(tmp_path))
    
    with patch('sqlite3.connect', side_effect=sqlite3.OperationalError("database is locked")):
        try:
            manager.save_version(str(tmp_path / "main.py"), "test")
            crashed = False
        except sqlite3.OperationalError:
            crashed = True
            
        assert not crashed