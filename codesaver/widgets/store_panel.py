# -*- coding: utf-8 -*-
# codesaver/widgets/store_panel.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ..core.theme_manager import ThemeColors

class StorePanel(QWidget):
    """Placeholder Panel for the Future Plugin & API Store"""
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.mw = main_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)

        self.lbl_icon = QLabel("🛒")
        self.lbl_icon.setFont(QFont("Segoe UI Emoji", 64))
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_icon)

        self.lbl_title = QLabel("Plugin & API Store")
        self.lbl_title.setFont(QFont("Consolas", 16, QFont.Weight.Bold))
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_title)

        self.lbl_warning = QLabel(
            "This section is currently disabled.\n"
            "We are building an amazing marketplace for you.\n"
            "It will be available in future updates!"
        )
        self.lbl_warning.setFont(QFont("Consolas", 11))
        self.lbl_warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # 🚀 CHANGED: Using semantic warning color
        self.lbl_warning.setStyleSheet(f"color: {ThemeColors.WARNING}; margin-top: 10px; line-height: 1.5; background: transparent; border: none;")
        layout.addWidget(self.lbl_warning)