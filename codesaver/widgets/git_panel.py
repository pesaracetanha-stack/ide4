# -*- coding: utf-8 -*-
# codesaver/widgets/git_panel.py
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QTextEdit, QListWidget, QLabel, QListWidgetItem, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon

# 🚀 NEW: Import central theme colors
from ..core.theme_manager import ThemeColors


class GitPanel(QWidget):
    """Visual Git Integration Panel (Source Control)"""
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.mw = main_window
        self.setup_ui()
        # 🚀 REMOVED: self.apply_theme() is no longer needed!

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()
        self.lbl_title = QLabel("SOURCE CONTROL")
        self.lbl_title.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        header_layout.addWidget(self.lbl_title)
        
        self.btn_refresh = QPushButton("🔄 Refresh")
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.refresh_status)
        header_layout.addWidget(self.btn_refresh)
        layout.addLayout(header_layout)

        # Commit Message Input
        self.commit_msg_input = QTextEdit()
        self.commit_msg_input.setPlaceholderText("Message (Ctrl+Enter to commit)")
        self.commit_msg_input.setMaximumHeight(80)
        layout.addWidget(self.commit_msg_input)

        # Action Buttons
        btn_layout = QHBoxLayout()
        self.btn_commit = QPushButton("✓ Commit")
        self.btn_commit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_commit.clicked.connect(self.perform_commit)
        
        self.btn_push = QPushButton("↑ Push")
        self.btn_push.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_push.clicked.connect(self.perform_push)
        
        btn_layout.addWidget(self.btn_commit)
        btn_layout.addWidget(self.btn_push)
        layout.addLayout(btn_layout)

        # Changes List
        self.lbl_changes = QLabel("CHANGES")
        self.lbl_changes.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        self.lbl_changes.setStyleSheet("margin-top: 10px; background: transparent; border: none;")
        layout.addWidget(self.lbl_changes)

        self.changes_list = QListWidget()
        layout.addWidget(self.changes_list, stretch=1)

    # 🚀 REMOVED: apply_theme() completely!

    def update_changes_list(self):
        self.changes_list.clear()
        git_states = getattr(self.mw.git_mgr, 'git_states', {})
        
        if not git_states:
            item = QListWidgetItem("No changes detected.")
            item.setForeground(QColor(ThemeColors.TEXT_MUTED))
            self.changes_list.addItem(item)
            return

        for path, state in git_states.items():
            filename = os.path.basename(path)
            rel_path = os.path.relpath(path, self.mw.project_root)
            
            item = QListWidgetItem(f"{state.ljust(3)} {filename}")
            item.setToolTip(rel_path)
            
            # 🚀 CHANGED: Apply semantic colors from central ThemeColors
            if state in ('M', 'AM', 'MM'): 
                item.setForeground(QColor(ThemeColors.WARNING))
            elif state in ('??', 'A'): 
                item.setForeground(QColor(ThemeColors.SUCCESS))
            elif state in ('D', 'AD'): 
                item.setForeground(QColor(ThemeColors.ERROR))
            else:
                item.setForeground(QColor(ThemeColors.TEXT_MAIN))
                
            self.changes_list.addItem(item)
            
        self.lbl_changes.setText(f"CHANGES ({len(git_states)})")

    def refresh_status(self):
        if self.mw.project_root:
            self.mw.git_mgr.update_git_status(self.mw.project_root)

    def perform_commit(self):
        msg = self.commit_msg_input.toPlainText().strip()
        if not msg:
            QMessageBox.warning(self, "Git Commit", "Please enter a commit message.")
            return
            
        success, output = self.mw.git_mgr.git_commit_all(self.mw.project_root, msg)
        if success:
            self.commit_msg_input.clear()
            self.refresh_status()
            if hasattr(self.mw, 'status_label'):
                self.mw.status_label.setText("Git Commit Successful!")
        else:
            QMessageBox.critical(self, "Git Error", f"Commit failed:\n{output}")

    def perform_push(self):
        if hasattr(self.mw, 'status_label'):
            self.mw.status_label.setText("Pushing to remote...")
            
        success, output = self.mw.git_mgr.git_push(self.mw.project_root)
        if success:
            QMessageBox.information(self, "Git Push", "Successfully pushed to remote repository.")
            if hasattr(self.mw, 'status_label'):
                self.mw.status_label.setText("Git Push Successful!")
        else:
            QMessageBox.critical(self, "Git Error", f"Push failed:\n{output}")