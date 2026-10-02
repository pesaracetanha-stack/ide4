# -*- coding: utf-8 -*-
# codesaver/tests/test_integration.py
import pytest
from PySide6.QtWidgets import QTreeView, QTabWidget
from codesaver.main import MainWindow

def test_full_application_startup_and_integrity(qtbot):
    """تست یکپارچگی: بوت شدن کامل نرم‌افزار و بررسی سلامت پنل‌ها با Type Checking"""
    window = MainWindow()
    qtbot.addWidget(window)
    
    assert "Code Saver - IDE Master v4.0" in window.windowTitle(), "Main window failed to set the correct title!"
    
    assert isinstance(window.editor_tab_widget, QTabWidget), "Editor tab widget is not properly initialized!"
    assert window.editor_tab_widget.count() > 0, "Application started without any tabs!"
    assert window.editor_tab_widget.tabText(0) == "Home", "Welcome screen did not load correctly!"
    
    assert isinstance(window.tree, QTreeView), "Project Explorer (Tree) is not a valid QTreeView!"
    assert window.terminal is not None, "Integrated Terminal failed to initialize!"
    assert window.git_panel is not None, "Git UI Panel failed to initialize!"
    assert window.chatbot_panel is not None, "AI Chatbot Panel failed to initialize!"
    assert window.arch_map is not None, "Architecture Map panel failed to initialize!"
    
    assert window.project_mgr is not None, "Project Manager failed to attach to the Main Window!"