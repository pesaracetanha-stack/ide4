# -*- coding: utf-8 -*-
# codesaver/widgets/snippet_panel.py
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QPlainTextEdit, QLineEdit, QListWidget, QLabel, QMessageBox, QListWidgetItem)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ..core.snippet_manager import SnippetManager

class SnippetPanel(QWidget):
    """Visual Snippet Manager Panel for the Sidebar"""
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.mw = main_window
        self.manager = SnippetManager()
        self.setup_ui()
        self.load_list()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        header_layout = QHBoxLayout()
        self.lbl_title = QLabel("SNIPPET MANAGER")
        self.lbl_title.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        header_layout.addWidget(self.lbl_title)
        
        self.btn_refresh = QPushButton("🔄 Reload")
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.load_list)
        header_layout.addWidget(self.btn_refresh)
        layout.addLayout(header_layout)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search snippets...")
        self.search_input.textChanged.connect(self.filter_list)
        layout.addWidget(self.search_input)

        self.snippet_list = QListWidget()
        self.snippet_list.itemClicked.connect(self.on_snippet_selected)
        layout.addWidget(self.snippet_list, stretch=1)

        self.lbl_editor = QLabel("EDIT SNIPPET")
        self.lbl_editor.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        self.lbl_editor.setStyleSheet("margin-top: 10px; background: transparent; border: none;")
        layout.addWidget(self.lbl_editor)

        self.trigger_input = QLineEdit()
        self.trigger_input.setPlaceholderText("Trigger word (e.g., class_qt)")
        layout.addWidget(self.trigger_input)

        self.code_input = QPlainTextEdit()
        self.code_input.setPlaceholderText("Snippet code...\nUse ${1:var} for variables.")
        self.code_input.setMaximumHeight(150)
        layout.addWidget(self.code_input)

        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("💾 Save / Update")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.clicked.connect(self.save_snippet)
        
        self.btn_delete = QPushButton("🗑️ Delete")
        self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete.clicked.connect(self.delete_snippet)
        
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_delete)
        layout.addLayout(btn_layout)

        self.btn_clear = QPushButton("✨ New Snippet")
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.clicked.connect(self.clear_inputs)
        layout.addWidget(self.btn_clear)

    def load_list(self):
        self.manager.load_snippets()
        self.snippet_list.clear()
        
        for trigger in sorted(self.manager.snippets.keys()):
            item = QListWidgetItem(trigger)
            self.snippet_list.addItem(item)
            
        self.lbl_title.setText(f"SNIPPETS ({len(self.manager.snippets)})")

    def filter_list(self, text):
        search_text = text.lower()
        for i in range(self.snippet_list.count()):
            item = self.snippet_list.item(i)
            item.setHidden(search_text not in item.text().lower())

    def on_snippet_selected(self, item):
        trigger = item.text()
        code = self.manager.get_snippet(trigger)
        if code is not None:
            self.trigger_input.setText(trigger)
            self.code_input.setPlainText(code)

    def save_snippet(self):
        trigger = self.trigger_input.text().strip()
        code = self.code_input.toPlainText().strip()
        
        if not trigger or not code:
            QMessageBox.warning(self, "Warning", "Both Trigger word and Code are required.")
            return
            
        self.manager.add_snippet(trigger, code)
        self.load_list()
        
        items = self.snippet_list.findItems(trigger, Qt.MatchFlag.MatchExactly)
        if items:
            self.snippet_list.setCurrentItem(items[0])
            
        if hasattr(self.mw, 'status_label'):
            self.mw.status_label.setText(f"Snippet '{trigger}' saved.")

    def delete_snippet(self):
        trigger = self.trigger_input.text().strip()
        if not trigger:
            return
            
        reply = QMessageBox.question(self, "Delete Snippet", f"Are you sure you want to delete '{trigger}'?")
        if reply == QMessageBox.StandardButton.Yes:
            self.manager.delete_snippet(trigger)
            self.clear_inputs()
            self.load_list()
            if hasattr(self.mw, 'status_label'):
                self.mw.status_label.setText(f"Snippet '{trigger}' deleted.")

    def clear_inputs(self):
        self.snippet_list.clearSelection()
        self.trigger_input.clear()
        self.code_input.clear()
        self.trigger_input.setFocus()