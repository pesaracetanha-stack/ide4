# -*- coding: utf-8 -*-
# codesaver/widgets/version_history_dock.py
import os
from PySide6.QtWidgets import QDockWidget, QListWidget, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Signal, Qt

from ..core.theme_manager import ThemeColors

class VersionHistoryDock(QDockWidget):
    version_selected = Signal(str, object) 

    def __init__(self, parent=None):
        super().__init__("Version History", parent)
        self.current_file = None
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.info_label = QLabel("No file selected")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; margin-bottom: 5px;")
        layout.addWidget(self.info_label)
        
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.list_widget)
        
        self.setWidget(widget)

    def set_current_file(self, file_path):
        self.current_file = file_path
        if file_path:
            name = os.path.basename(file_path)
            self.info_label.setText(f"Changes for:\n{name}")
        else:
            self.info_label.setText("No file selected")
            self.list_widget.clear()

    def load_versions(self, versions):
        self.list_widget.clear()
        if not versions:
            self.list_widget.addItem("No versions found.")
            return
            
        for dt in versions:
            display = dt.strftime("%Y-%m-%d %H:%M:%S")
            self.list_widget.addItem(display)
            item = self.list_widget.item(self.list_widget.count() - 1)
            item.setData(Qt.ItemDataRole.UserRole, dt)

    def _on_item_double_clicked(self, item):
        if not self.current_file: return
        dt = item.data(Qt.ItemDataRole.UserRole)
        if dt:
            self.version_selected.emit(self.current_file, dt)