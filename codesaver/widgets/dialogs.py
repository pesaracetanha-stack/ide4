# -*- coding: utf-8 -*-
# codesaver/widgets/dialogs.py
import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
                               QLabel, QPushButton, QFileDialog, QDialogButtonBox, 
                               QMessageBox, QListWidget)
from PySide6.QtCore import Qt

from ..core.theme_manager import ThemeColors

class ProfileDialog(QDialog):
    def __init__(self, config_mgr, parent=None):
        super().__init__(parent)
        self.config_mgr = config_mgr
        
        self.setWindowTitle("User Profile")
        self.setFixedSize(400, 250)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        info_label = QLabel("Authentication is currently disabled.")
        info_label.setStyleSheet(f"color: {ThemeColors.ERROR}; font-style: italic; font-weight: bold;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        user_layout = QHBoxLayout()
        user_label = QLabel("Username:")
        user_label.setFixedWidth(120)
        self.user_edit = QLineEdit(self.config_mgr.username)
        self.user_edit.setReadOnly(True)
        user_layout.addWidget(user_label)
        user_layout.addWidget(self.user_edit)
        layout.addLayout(user_layout)

        email_layout = QHBoxLayout()
        email_label = QLabel("Email:")
        email_label.setFixedWidth(120)
        self.email_edit = QLineEdit(self.config_mgr.email)
        self.email_edit.setReadOnly(True)
        email_layout.addWidget(email_label)
        email_layout.addWidget(self.email_edit)
        layout.addLayout(email_layout)

        days_layout = QHBoxLayout()
        days_label = QLabel("Days Remaining:")
        days_label.setFixedWidth(120)
        self.days_edit = QLineEdit(str(self.config_mgr.days_remaining))
        self.days_edit.setReadOnly(True)
        days_layout.addWidget(days_label)
        days_layout.addWidget(self.days_edit)
        layout.addLayout(days_layout)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.login_btn = QPushButton("Signup / Signin")
        self.login_btn.setEnabled(False) 
        btn_layout.addWidget(self.login_btn)
        layout.addLayout(btn_layout)

class ProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Open Project")
        self.setFixedSize(450, 120)
        layout = QVBoxLayout(self)
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Project folder path...")
        path_layout.addWidget(self.path_edit)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(self.validate_and_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
        self.selected_path = None

    def browse(self):
        default_dir = os.path.expanduser("~/Desktop")
        folder = QFileDialog.getExistingDirectory(self, "Select Project Folder", default_dir)
        if folder:
            self.path_edit.setText(folder)

    def validate_and_accept(self):
        path = self.path_edit.text().strip()
        if not path or not os.path.isdir(path):
            QMessageBox.warning(self, "Invalid Path", "Please select a valid folder.")
            return
        self.selected_path = path
        self.accept()

class RestorePointDialog(QDialog):
    def __init__(self, parent=None, restore_points=None):
        super().__init__(parent)
        self.setWindowTitle("Restore Points")
        self.setMinimumSize(400, 300)
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        if restore_points:
            for name, timestamp in restore_points:
                self.list_widget.addItem(f"{name} ({timestamp})")
        layout.addWidget(self.list_widget)
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def get_selected(self):
        current = self.list_widget.currentItem()
        if current:
            return current.text()
        return None