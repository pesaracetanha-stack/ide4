# -*- coding: utf-8 -*-
# codesaver/tests/test_project_manager.py
import pytest
from PySide6.QtCore import QObject
from unittest.mock import patch, MagicMock
from core.project_manager import ProjectManager

class FakeMainWindow(QObject):
    pass

def test_project_manager_creates_file_physically(tmp_path):
    mw = FakeMainWindow()
    mw.tree = MagicMock()
    mw.tree.get_selected_path.return_value = str(tmp_path)
    
    pm = ProjectManager(mw)
    pm.project_root = str(tmp_path)

    with patch('PySide6.QtWidgets.QInputDialog.getText', return_value=('new_script.py', True)):
        pm.create_new_file()

    created_file = tmp_path / 'new_script.py'
    assert created_file.exists()

def test_project_manager_survives_os_permission_denied(tmp_path):
    mw = FakeMainWindow()
    mw.tree = MagicMock()
    mw.tree.get_selected_path.return_value = str(tmp_path)
    pm = ProjectManager(mw)
    pm.project_root = str(tmp_path)

    with patch('PySide6.QtWidgets.QInputDialog.getText', return_value=('locked.py', True)):
        with patch('builtins.open', side_effect=PermissionError("Access is denied")):
            with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_error_box:
                pm.create_new_file()
                mock_error_box.assert_called_once()