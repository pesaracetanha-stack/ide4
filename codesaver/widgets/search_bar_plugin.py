# -*- coding: utf-8 -*-
# codesaver/widgets/search_bar_plugin.py
import os
from PySide6.QtWidgets import QToolBar, QLineEdit, QCompleter, QWidget, QSizePolicy
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtCore import Qt, QStringListModel

from ..core.theme_manager import ThemeColors

class GlobalSearchBar:
    def __init__(self, main_window):
        self.mw = main_window
        self.file_list = []
        self.setup_ui()

    def setup_ui(self):
        self.search_toolbar = QToolBar("Global Search")
        self.search_toolbar.setMovable(False)
        self.search_toolbar.setStyleSheet("QToolBar { border: none; padding: 5px; }")
        self.mw.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.search_toolbar)
        
        spacer_left = QWidget()
        spacer_left.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        spacer_right = QWidget()
        spacer_right.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Quick File Search (Ctrl+P)...")
        self.search_input.setMinimumWidth(400)
        self.search_input.setMaximumWidth(600)
        # Removed hardcoded styles, let ThemeManager handle it
        
        self.search_toolbar.addWidget(spacer_left)
        self.search_toolbar.addWidget(self.search_input)
        self.search_toolbar.addWidget(spacer_right)
        
        self.completer_model = QStringListModel()
        self.completer = QCompleter(self.completer_model, self.mw)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.completer.setMaxVisibleItems(10)
        
        self.search_input.setCompleter(self.completer)
        
        self.shortcut = QShortcut(QKeySequence("Ctrl+P"), self.mw)
        self.shortcut.activated.connect(self.focus_search)
        
        self.completer.activated.connect(self.open_selected_file)

    def focus_search(self):
        self.update_file_list()
        self.search_input.setFocus()
        self.search_input.selectAll()

    def update_file_list(self):
        if not hasattr(self.mw, 'project_mgr') or not self.mw.project_mgr.project_root:
            return
            
        root = self.mw.project_mgr.project_root
        files = []
        
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if not d.startswith('.') and d not in ('__pycache__', 'venv', 'env', 'node_modules')]
            for f in filenames:
                full_path = os.path.join(dirpath, f)
                rel_path = os.path.relpath(full_path, root)
                files.append(rel_path)
                
        self.file_list = files
        self.completer_model.setStringList(self.file_list)

    def open_selected_file(self, rel_path):
        if not hasattr(self.mw, 'project_mgr') or not self.mw.project_mgr.project_root:
            return
            
        full_path = os.path.join(self.mw.project_mgr.project_root, rel_path)
        if os.path.exists(full_path):
            if hasattr(self.mw, 'tab_mgr'):
                self.mw.tab_mgr.open_file_in_tab(full_path)
            self.search_input.clear()
            self.search_input.clearFocus()