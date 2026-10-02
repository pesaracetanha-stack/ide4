# -*- coding: utf-8 -*-
# codesaver/widgets/plugin_panel.py
import os
import shutil
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QListWidget, QLabel, QListWidgetItem, QMessageBox, QFileDialog)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QColor, QFont

class PluginPanel(QWidget):
    """Visual Extension Manager Panel"""
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.mw = main_window
        self.setup_ui()
        self.apply_theme()
        
        # Need to safely get plugin manager instance from main window
        self.plugin_mgr = getattr(self.mw, 'plugin_mgr', None)
        self.load_plugins()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()
        self.lbl_title = QLabel("EXTENSIONS")
        self.lbl_title.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        header_layout.addWidget(self.lbl_title)
        
        self.btn_refresh = QPushButton("🔄 Refresh")
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.load_plugins)
        header_layout.addWidget(self.btn_refresh)
        layout.addLayout(header_layout)

        # Action Buttons
        self.btn_install = QPushButton("📥 Install from VSIX/PY...")
        self.btn_install.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_install.clicked.connect(self.install_new_plugin)
        layout.addWidget(self.btn_install)

        self.lbl_info = QLabel("Check/Uncheck to enable or disable plugins.")
        self.lbl_info.setStyleSheet("font-size: 11px; margin-top: 10px;")
        layout.addWidget(self.lbl_info)

        # Plugin List
        self.plugin_list = QListWidget()
        self.plugin_list.itemChanged.connect(self.on_plugin_toggled)
        layout.addWidget(self.plugin_list, stretch=1)

    def apply_theme(self):
        theme = QSettings("GitiArts", "CodeSaver_Theme")
        app_bg = theme.value("app_bg", "#1e1e2e")
        text_color = theme.value("text_color", "#cdd6f4")
        menu_bg = theme.value("menu_bg", "#11111b")
        menu_selected = theme.value("menu_selected", "#89b4fa")

        self.setStyleSheet(f"""
            QWidget {{ background-color: {app_bg}; color: {text_color}; }}
            QLabel {{ color: #8b949e; }}
            QPushButton {{ 
                background-color: {menu_bg}; 
                color: {text_color}; 
                border: 1px solid #45475a; 
                border-radius: 4px; 
                padding: 6px; 
                font-weight: bold; 
            }}
            QPushButton:hover {{ background-color: {menu_selected}; color: #11111b; }}
            QListWidget {{ 
                background-color: {menu_bg}; 
                border: 1px solid #45475a; 
                border-radius: 4px;
                outline: none; 
            }}
            QListWidget::item {{ 
                padding: 10px; 
                border-bottom: 1px solid #30363d; 
            }}
            QListWidget::item:hover {{ background-color: rgba(255, 255, 255, 0.05); }}
            QListWidget::item:selected {{ background-color: transparent; }}
            QListWidget::indicator {{ width: 18px; height: 18px; border: 1px solid #8b949e; border-radius: 3px; background-color: #11111b; }}
            QListWidget::indicator:checked {{ background-color: {menu_selected}; border: 1px solid {menu_selected}; image: url(codesaver_icons/check.svg); }}
        """)

    def load_plugins(self):
        if not self.plugin_mgr: return
        self.plugin_list.blockSignals(True)
        self.plugin_list.clear()
        
        available = self.plugin_mgr.get_available_plugins()
        
        for filename, is_enabled in available.items():
            item = QListWidgetItem(f"🧩 {filename}")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if is_enabled else Qt.CheckState.Unchecked)
            
            # Dim the text if disabled
            if not is_enabled:
                item.setForeground(QColor("#6e738d"))
            else:
                item.setForeground(QColor("#a6e3a1"))
                
            self.plugin_list.addItem(item)
            
        self.lbl_title.setText(f"EXTENSIONS ({len(available)})")
        self.plugin_list.blockSignals(False)

    def on_plugin_toggled(self, item):
        if not self.plugin_mgr: return
        
        filename = item.text().replace("🧩 ", "")
        is_enabled = item.checkState() == Qt.CheckState.Checked
        
        self.plugin_mgr.toggle_plugin_state(filename, is_enabled)
        
        if is_enabled:
            item.setForeground(QColor("#a6e3a1"))
        else:
            item.setForeground(QColor("#6e738d"))
            
        QMessageBox.information(self, "Restart Required", 
                                f"Plugin status updated.\nPlease restart the application for changes to take effect.")

    def install_new_plugin(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Select Plugin File", "", "Python Files (*.py)")
        if filepath and self.plugin_mgr:
            try:
                shutil.copy(filepath, self.plugin_mgr.plugins_dir)
                self.load_plugins()
                QMessageBox.information(self, "Success", "Extension installed successfully.\nPlease restart the application to activate it.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to install extension:\n{str(e)}")