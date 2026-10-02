# -*- coding: utf-8 -*-
# codesaver/tests/test_config_manager.py
import os
import pytest
from core.config import ConfigManager

def test_config_manager_handles_corrupt_json(tmp_path):
    corrupt_config = tmp_path / "config.json"
    corrupt_config.write_text("{ invalid json [", encoding="utf-8")
    
    manager = ConfigManager()
    manager.config_file = str(corrupt_config)
    
    manager.load() # نباید کرش کند
    assert manager.font_size > 0

def test_config_manager_handles_wrong_types_and_readonly(tmp_path):
    corrupt_config = tmp_path / "config2.json"
    corrupt_config.write_text('{"font_size": "large"}', encoding="utf-8")
    os.chmod(str(corrupt_config), 0o444) # Read-Only
    
    manager = ConfigManager()
    manager.config_file = str(corrupt_config)
    
    manager.load()
    assert isinstance(manager.font_size, int)
    
    try:
        manager.save()
        crashed = False
    except PermissionError:
        crashed = True
        
    assert not crashed