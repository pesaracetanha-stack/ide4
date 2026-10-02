# -*- coding: utf-8 -*-
# codesaver/widgets/diff_dialog.py
import os
import difflib
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel
from PySide6.QtGui import QColor, QTextCharFormat
from PySide6.QtCore import Qt

from ..core.theme_manager import ThemeColors

class DiffDialog(QDialog):
    def __init__(self, file_path, old_text, new_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Review Changes Before Saving - {os.path.basename(file_path)}")
        self.setMinimumSize(800, 550)

        layout = QVBoxLayout(self)
        
        lbl = QLabel("Please review the differences between the current disk version and your unsaved changes to ensure a secure development workflow:")
        layout.addWidget(lbl)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.text_edit)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel (Keep Unsaved)")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Accept and Save to Disk")
        save_btn.setStyleSheet(f"background-color: {ThemeColors.ACCENT_TEAL}; color: {ThemeColors.BG_BASE}; border: none;")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

        self._generate_diff(old_text, new_text)

    def _generate_diff(self, old_text, new_text):
        old_lines = old_text.splitlines()
        new_lines = new_text.splitlines()

        diff = difflib.unified_diff(
            old_lines, new_lines, 
            fromfile='Disk Version', 
            tofile='Memory Version', 
            lineterm='', n=3
        )
        
        cursor = self.text_edit.textCursor()
        
        fmt_add = QTextCharFormat()
        fmt_add.setBackground(QColor(35, 75, 35))
        fmt_add.setForeground(QColor(80, 200, 80))

        fmt_remove = QTextCharFormat()
        fmt_remove.setBackground(QColor(80, 25, 25))
        fmt_remove.setForeground(QColor(255, 100, 100))

        fmt_header = QTextCharFormat()
        fmt_header.setForeground(QColor(ThemeColors.ACCENT_BLUE))

        fmt_normal = QTextCharFormat()
        fmt_normal.setForeground(QColor(ThemeColors.TEXT_MAIN))

        for line in diff:
            if line.startswith('+++') or line.startswith('---') or line.startswith('@@'):
                cursor.insertText(line + '\n', fmt_header)
            elif line.startswith('+'):
                cursor.insertText(line + '\n', fmt_add)
            elif line.startswith('-'):
                cursor.insertText(line + '\n', fmt_remove)
            else:
                cursor.insertText(line + '\n', fmt_normal)