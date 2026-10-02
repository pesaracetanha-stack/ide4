# -*- coding: utf-8 -*-
# codesaver/widgets/preferences_dialog.py
import os
import json
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
                               QStackedWidget, QWidget, QLabel, QPushButton, 
                               QFontComboBox, QComboBox, QFormLayout, 
                               QGroupBox, QFileDialog, QScrollArea, QColorDialog, QMessageBox, QApplication)
from PySide6.QtCore import Qt, QSettings, QSize
from PySide6.QtGui import QFont, QColor

from ..core.theme_manager import ThemeIcons, ThemeColors, ThemeManager

class PreferencesDialog(QDialog):
    def __init__(self, config_mgr, parent=None):
        super().__init__(parent)
        self.config_mgr = config_mgr
        self.mw = parent
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.icon_dir = os.path.join(base_dir, "codesaver_icons")
        
        self.setWindowTitle("Preferences & Theme Studio")
        self.resize(850, 600)
        
        self.default_colors = {
            "bg_base": "#1a1c23",
            "bg_panel": "#1e1e2e",
            "bg_input": "#11111b",
            "text_main": "#cdd6f4",
            "text_muted": "#a6adc8",
            "accent_teal": "#4fd1c5",
            "accent_blue": "#89b4fa",
            "error": "#f38ba8",
            "success": "#a6e3a1",
            "icon_color": "#cdd6f4" # 🚀 NEW
        }
        
        self.studio_colors = {}
        self.color_buttons = {}
        
        self._load_current_theme()
        self.setup_ui()

    def _load_current_theme(self):
        settings = QSettings("GitiArts", "CodeSaver_Theme")
        for key, default_val in self.default_colors.items():
            self.studio_colors[key] = settings.value(f"theme_{key}", default_val)

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(220)
        self.sidebar.setIconSize(QSize(22, 22))
        
        icon_color = ThemeColors.ACCENT_TEAL
        
        categories = [
            ("General & Fonts", "general_settings.svg"),
            ("Theme Studio", "editor_colors.svg"), 
            ("Hidden Folders", "toggle_hidden_folder.svg")
        ]
        
        for text, icon_name in categories:
            colored_icon = ThemeIcons.get_icon(icon_name, icon_color)
            item = QListWidgetItem(colored_icon, f"  {text}")
            self.sidebar.addItem(item)

        self.sidebar.currentRowChanged.connect(self.change_page)
        main_layout.addWidget(self.sidebar)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)

        self.pages = QStackedWidget()
        right_layout.addWidget(self.pages)

        self.pages.addWidget(self._create_general_page())
        self.pages.addWidget(self._create_theme_studio_page())
        self.pages.addWidget(self._create_hidden_folders_page())

        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("Apply & Save")
        btn_save.setStyleSheet(f"background-color: {ThemeColors.ACCENT_TEAL}; color: {ThemeColors.BG_BASE}; border: none;")
        btn_save.clicked.connect(self.save_and_apply)
        
        bottom_layout.addWidget(btn_cancel)
        bottom_layout.addWidget(btn_save)
        
        right_layout.addLayout(bottom_layout)
        main_layout.addWidget(right_panel)
        
        self.sidebar.setCurrentRow(0)

    def _create_scrollable_page(self, layout_func):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        layout_func(content_layout)
        content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        return page

    def change_page(self, index):
        self.pages.setCurrentIndex(index)

    def _create_general_page(self):
        def build(layout):
            group = QGroupBox("Editor & Typography")
            form = QFormLayout(group)
            form.setSpacing(15)
            
            self.font_combo = QFontComboBox()
            self.font_combo.setCurrentText(self.config_mgr.font_family)
            form.addRow("Editor Font Family:", self.font_combo)
            
            self.size_combo = QComboBox()
            sizes = {
                "Very Small (10)": 10, "Small (12)": 12, "Medium (14)": 14,
                "Large (18)": 18, "Extra Large (24)": 24
            }
            for text, val in sizes.items(): self.size_combo.addItem(text, val)
                
            idx = self.size_combo.findData(self.config_mgr.font_size)
            self.size_combo.setCurrentIndex(idx if idx >= 0 else 1)
            form.addRow("Font Size:", self.size_combo)
            layout.addWidget(group)
            
        return self._create_scrollable_page(build)

    def _create_theme_studio_page(self):
        def build(layout):
            action_layout = QHBoxLayout()
            
            btn_import = QPushButton("📂 Import JSON")
            btn_import.clicked.connect(self.import_theme)
            
            btn_export = QPushButton("💾 Export JSON")
            btn_export.clicked.connect(self.export_theme)
            
            btn_reset = QPushButton("🔄 Reset Default")
            btn_reset.setStyleSheet(f"color: {ThemeColors.ERROR}; background: transparent; border: 1px dashed {ThemeColors.ERROR};")
            btn_reset.clicked.connect(self.reset_theme)
            
            action_layout.addWidget(btn_import)
            action_layout.addWidget(btn_export)
            action_layout.addStretch()
            action_layout.addWidget(btn_reset)
            layout.addLayout(action_layout)

            core_group = QGroupBox("Core Interface Colors")
            core_form = QFormLayout(core_group)
            core_form.setSpacing(10)
            self._add_color_picker("Main Background (Base):", "bg_base", core_form)
            self._add_color_picker("Panels & Sidebars:", "bg_panel", core_form)
            self._add_color_picker("Inputs & Fields:", "bg_input", core_form)
            self._add_color_picker("Main Text:", "text_main", core_form)
            self._add_color_picker("Muted/Disabled Text:", "text_muted", core_form)
            self._add_color_picker("General Icons Color:", "icon_color", core_form) # 🚀 NEW
            layout.addWidget(core_group)

            accent_group = QGroupBox("Brand & Accents")
            accent_form = QFormLayout(accent_group)
            accent_form.setSpacing(10)
            self._add_color_picker("Primary Accent (Teal):", "accent_teal", accent_form)
            self._add_color_picker("Secondary Accent (Blue):", "accent_blue", accent_form)
            self._add_color_picker("Error / Destructive:", "error", accent_form)
            self._add_color_picker("Success / Additions:", "success", accent_form)
            layout.addWidget(accent_group)

        return self._create_scrollable_page(build)

    def _add_color_picker(self, label, key, form):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl = QLabel(label)
        btn = QPushButton()
        btn.setFixedSize(60, 25)
        
        color = self.studio_colors.get(key, "#ffffff")
        btn.setStyleSheet(f"background-color: {color}; border: 1px solid #fff; border-radius: 4px;")
        btn.clicked.connect(lambda _, k=key, b=btn: self.pick_color(k, b))
        
        self.color_buttons[key] = btn
        row_layout.addWidget(lbl)
        row_layout.addStretch()
        row_layout.addWidget(btn)
        form.addRow(row_widget)

    def pick_color(self, key, btn):
        initial = QColor(self.studio_colors.get(key, "#ffffff"))
        color = QColorDialog.getColor(initial, self, "Select Theme Color")
        if color.isValid():
            hex_code = color.name()
            self.studio_colors[key] = hex_code
            btn.setStyleSheet(f"background-color: {hex_code}; border: 1px solid #fff; border-radius: 4px;")

    def reset_theme(self):
        reply = QMessageBox.question(self, "Reset Theme", "Are you sure you want to revert to the default IDE theme?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.studio_colors = self.default_colors.copy()
            self._refresh_color_buttons()

    def export_theme(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Theme", "MyCustomTheme.json", "JSON Files (*.json)")
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(self.studio_colors, f, indent=4)
                QMessageBox.information(self, "Success", "Theme exported successfully! You can share this JSON file.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save theme:\n{e}")

    def import_theme(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Theme", "", "JSON Files (*.json)")
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    loaded_theme = json.load(f)
                
                for key in self.default_colors.keys():
                    if key in loaded_theme:
                        self.studio_colors[key] = loaded_theme[key]
                
                self._refresh_color_buttons()
                QMessageBox.information(self, "Success", "Theme imported successfully. Click 'Apply & Save' to see changes.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Invalid theme file format:\n{e}")

    def _refresh_color_buttons(self):
        for key, btn in self.color_buttons.items():
            color = self.studio_colors.get(key, "#ffffff")
            btn.setStyleSheet(f"background-color: {color}; border: 1px solid #fff; border-radius: 4px;")

    def _create_hidden_folders_page(self):
        def build(layout):
            group = QGroupBox("Hidden Folders Management")
            vbox = QVBoxLayout(group)
            
            self.hidden_list = QListWidget()
            for f in self.config_mgr.hidden_folders:
                self.hidden_list.addItem(f)
            vbox.addWidget(self.hidden_list)
            
            btn_layout = QHBoxLayout()
            btn_add = QPushButton("➕ Add Folder")
            btn_add.clicked.connect(self.add_hidden_folder)
            btn_rem = QPushButton("🗑️ Remove Selected")
            btn_rem.clicked.connect(self.remove_hidden_folder)
            
            btn_layout.addWidget(btn_add)
            btn_layout.addWidget(btn_rem)
            vbox.addLayout(btn_layout)
            layout.addWidget(group)
            
        return self._create_scrollable_page(build)

    def add_hidden_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select folder to hide")
        if folder:
            items = [self.hidden_list.item(i).text() for i in range(self.hidden_list.count())]
            if folder not in items:
                self.hidden_list.addItem(folder)

    def remove_hidden_folder(self):
        item = self.hidden_list.currentItem()
        if item:
            self.hidden_list.takeItem(self.hidden_list.row(item))

    def save_and_apply(self):
        self.config_mgr.font_family = self.font_combo.currentText()
        self.config_mgr.font_size = self.size_combo.currentData()
        
        hidden = [self.hidden_list.item(i).text() for i in range(self.hidden_list.count())]
        self.config_mgr.hidden_folders = hidden
        
        settings = QSettings("GitiArts", "CodeSaver_Theme")
        for key, color in self.studio_colors.items():
            settings.setValue(f"theme_{key}", color)
            
        # 🚀 Reload theme colors internally and apply the CSS
        ThemeColors.load_from_settings()
        QApplication.instance().setStyleSheet(ThemeManager.get_global_stylesheet())
        
        QMessageBox.information(self, "Theme Applied", "UI Theme applied live.\n\nNote: Icon color changes will fully take effect after restarting the IDE.")
        self.accept()