# -*- coding: utf-8 -*-
# codesaver/widgets/main_ui_builder.py
import sys
import os
from PySide6.QtWidgets import QStatusBar, QLabel, QProgressBar, QApplication
from PySide6.QtCore import QSettings

from .dock_builder import DockBuilder
from .menu_builder import MenuBuilder
from ..core.theme_manager import ThemeManager, ThemeColors

class UIBuilder:
    def __init__(self, main_window):
        self.mw = main_window
        if hasattr(sys, '_MEIPASS'):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.icon_dir = os.path.join(base_dir, "codesaver_icons")
        
        self.menu_builder = MenuBuilder(self.mw, self.icon_dir)

    def build_phase1_core(self):
        self.build_statusbar()
        DockBuilder.build_core_layout(self.mw)

    def build_phase2_menus(self):
        self.menu_builder.build_menu()
        self.menu_builder.build_toolbar()
        
        try:
            from .search_bar_plugin import GlobalSearchBar
            self.mw.global_search_bar = GlobalSearchBar(self.mw)
        except ImportError:
            pass
        
        self.apply_base_dark_theme()
        
    def build_recent_menu(self):
        self.menu_builder.build_recent_menu()

    def build_statusbar(self):
        if not hasattr(self.mw, 'status_bar') or self.mw.status_bar is None:
            self.mw.status_bar = QStatusBar()
            self.mw.setStatusBar(self.mw.status_bar)
            
            self.mw.status_label = QLabel("Ready")
            self.mw.status_bar.addPermanentWidget(self.mw.status_label)
            
            self.mw.progress_bar = QProgressBar()
            self.mw.progress_bar.setVisible(False)
            self.mw.progress_bar.setMinimumWidth(200)
            self.mw.status_bar.addPermanentWidget(self.mw.progress_bar)
            
            self.mw.creator_label = QLabel("Created by www.gitiarts.ir")
            # 🚀 CHANGED: Using ThemeColors instead of hardcoded hex
            self.mw.creator_label.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; margin-right: 15px; background: transparent;")
            self.mw.status_bar.addPermanentWidget(self.mw.creator_label)

    def apply_base_dark_theme(self):
        # 🚀 CHANGED: Injecting the Global Theme Manager's stylesheet centrally
        QApplication.instance().setStyleSheet(ThemeManager.get_global_stylesheet())