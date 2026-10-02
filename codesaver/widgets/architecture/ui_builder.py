# -*- coding: utf-8 -*-
# codesaver/widgets/architecture/ui_builder.py

from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QWidget, QLineEdit, 
                             QPushButton, QProgressBar, QTextEdit, QSplitter, QLabel, 
                             QScrollArea, QSlider, QFrame)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtCore import Qt
from ...core.theme_manager import ThemeColors

class ArchUIBuilder:
    """مسئول ساخت و چینش اِلمان‌های بصریِ تبِ معماری‌نگار"""
    def __init__(self, parent_tab):
        self.tab = parent_tab

    def build_ui(self):
        base_layout = QVBoxLayout(self.tab)
        base_layout.setContentsMargins(0, 0, 0, 0)
        
        self.tab.splitter = QSplitter(Qt.Orientation.Vertical)
        base_layout.addWidget(self.tab.splitter)
        
        top_widget = QWidget()
        main_layout = QVBoxLayout(top_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # --- Filters Area ---
        self.tab.scroll_area = QScrollArea()
        self.tab.scroll_area.setWidgetResizable(True)
        self.tab.scroll_area.setFixedHeight(50)
        self.tab.scroll_area.setStyleSheet(f"QScrollArea {{ border: none; background-color: transparent; }} QScrollBar:horizontal {{ height: 6px; background: {ThemeColors.BG_BASE}; }} QScrollBar::handle:horizontal {{ background: {ThemeColors.BORDER_DEFAULT}; border-radius: 3px; }}")
        
        self.tab.filter_container = QWidget()
        self.tab.filters_layout = QHBoxLayout(self.tab.filter_container)
        self.tab.filters_layout.setContentsMargins(0, 0, 0, 0)
        self.tab.scroll_area.setWidget(self.tab.filter_container)
        main_layout.addWidget(self.tab.scroll_area)
        
        # --- Toolbar ---
        tools_layout = QHBoxLayout()
        self.tab.search_input = QLineEdit()
        self.tab.search_input.setPlaceholderText("Search file...")
        self.tab.search_input.setStyleSheet(f"padding: 10px; border: 1px solid {ThemeColors.BORDER_DEFAULT}; border-radius: 6px; background-color: {ThemeColors.BG_INPUT};")
        
        self.tab.btn_watch = QPushButton("🔴 Live (Off)")
        self.tab.btn_watch.setCheckable(True)
        self.tab.btn_watch.setStyleSheet(f"QPushButton {{padding: 10px; background-color: {ThemeColors.BG_PANEL}; border-radius: 6px;}} QPushButton:checked {{background-color: {ThemeColors.ERROR}; color: white;}}")

        self.tab.btn_health = QPushButton("📊 Dashboard")
        self.tab.btn_draw = QPushButton("Refresh Map")
        self.tab.btn_draw.setStyleSheet(f"background-color: {ThemeColors.ACCENT_TEAL}; color: {ThemeColors.BG_BASE}; padding: 10px 20px; font-weight: bold; border-radius: 6px; border: none;")

        self.tab.btn_export_md = QPushButton("📄 Export MD")
        
        tools_layout.addWidget(self.tab.search_input, stretch=2)
        tools_layout.addWidget(self.tab.btn_export_md, stretch=1)
        tools_layout.addWidget(self.tab.btn_watch, stretch=1)
        tools_layout.addWidget(self.tab.btn_health, stretch=1)
        tools_layout.addWidget(self.tab.btn_draw, stretch=1)
        main_layout.addLayout(tools_layout)
        
        # --- Progress & Loading ---
        progress_layout = QHBoxLayout()
        self.tab.progress_bar = QProgressBar()
        self.tab.progress_bar.setStyleSheet(f"QProgressBar {{ border: 1px solid {ThemeColors.BORDER_ACTIVE}; border-radius: 6px; text-align: center; color: white; height: 12px; background-color: {ThemeColors.BG_INPUT};}} QProgressBar::chunk {{ background-color: {ThemeColors.ACCENT_BLUE}; border-radius: 4px; }}")
        self.tab.progress_bar.setVisible(False)
        
        self.tab.loading_label = QLabel("")
        self.tab.loading_label.setStyleSheet(f"color: {ThemeColors.WARNING}; font-weight: bold; font-size: 13px; background: transparent;")
        self.tab.loading_label.setVisible(False)
        
        progress_layout.addWidget(self.tab.progress_bar, stretch=1)
        progress_layout.addWidget(self.tab.loading_label)
        main_layout.addLayout(progress_layout)

        # --- Git Timeline Slider ---
        self.tab.git_frame = QFrame()
        self.tab.git_frame.setStyleSheet(f"background-color: {ThemeColors.BG_PANEL}; border: 1px solid {ThemeColors.BORDER_DEFAULT}; border-radius: 6px; padding: 5px;")
        git_layout = QHBoxLayout(self.tab.git_frame)
        self.tab.git_label = QLabel("Time Machine (Git):")
        self.tab.git_label.setStyleSheet(f"color: #a371f7; font-weight: bold; border: none; background: transparent;")
        
        self.tab.git_slider = QSlider(Qt.Orientation.Horizontal)
        self.tab.git_slider.setStyleSheet(f"QSlider::groove:horizontal {{ border: 1px solid {ThemeColors.BORDER_DEFAULT}; height: 8px; background: {ThemeColors.BG_BASE}; border-radius: 4px; }} QSlider::handle:horizontal {{ background: #a371f7; width: 14px; margin: -3px 0; border-radius: 7px; }}")
        self.tab.git_slider.setEnabled(False)
        
        self.tab.git_info = QLabel("Git not detected")
        self.tab.git_info.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; border: none; font-size: 11px; background: transparent;")
        
        git_layout.addWidget(self.tab.git_label)
        git_layout.addWidget(self.tab.git_slider, stretch=1)
        git_layout.addWidget(self.tab.git_info)
        self.tab.git_frame.setVisible(False) 
        main_layout.addWidget(self.tab.git_frame)
        
        # --- Web Browser (Vis.js Canvas) ---
        self.tab.browser = QWebEngineView()
        self.tab.browser.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        self.tab.browser.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        self.tab.browser.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        self.tab.browser.settings().setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        self.tab.browser.settings().setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
        main_layout.addWidget(self.tab.browser, stretch=1)

        # --- Log Console ---
        self.tab.log_console = QTextEdit()
        self.tab.log_console.setReadOnly(True)
        self.tab.log_console.setStyleSheet(f"background-color: {ThemeColors.BG_INPUT}; color: {ThemeColors.TEXT_MUTED}; border: 1px solid {ThemeColors.BORDER_DEFAULT}; font-family: Consolas, Tahoma; font-size: 11px;")
        
        self.tab.splitter.addWidget(top_widget)
        self.tab.splitter.addWidget(self.tab.log_console)
        self.tab.splitter.setSizes([750, 150])