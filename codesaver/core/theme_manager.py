# -*- coding: utf-8 -*-
# codesaver/core/theme_manager.py
import os
import sys
from PySide6.QtGui import QColor, QFont, QIcon, QPixmap, QPainter
from PySide6.QtCore import QByteArray, QSettings

class ThemeColors:
    """پالت رنگی داینامیک با قابلیت لود از تنظیمات"""
    BG_BASE = "#1a1c23"
    BG_PANEL = "#1e1e2e"
    BG_INPUT = "#11111b"
    BG_GLASS = "rgba(13, 25, 48, 0.6)"
    
    TEXT_MAIN = "#cdd6f4"
    TEXT_MUTED = "#a6adc8"
    TEXT_DISABLED = "#6e738d"
    
    BORDER_DEFAULT = "#313244"
    BORDER_ACTIVE = "#45475a"
    BORDER_GLASS = "rgba(255, 255, 255, 0.08)"
    
    ACCENT_TEAL = "#4fd1c5"
    ACCENT_BLUE = "#89b4fa"
    ACCENT_GOLD = "#ffd700"
    
    ERROR = "#f38ba8"
    SUCCESS = "#a6e3a1"
    WARNING = "#f9e2af"
    
    ICON_COLOR = "#cdd6f4" # 🚀 NEW: Default Icon Color

    @classmethod
    def load_from_settings(cls):
        """متدی برای بارگذاری رنگ‌های کاستوم کاربر از Theme Studio"""
        settings = QSettings("GitiArts", "CodeSaver_Theme")
        cls.BG_BASE = settings.value("theme_bg_base", "#1a1c23")
        cls.BG_PANEL = settings.value("theme_bg_panel", "#1e1e2e")
        cls.BG_INPUT = settings.value("theme_bg_input", "#11111b")
        cls.TEXT_MAIN = settings.value("theme_text_main", "#cdd6f4")
        cls.TEXT_MUTED = settings.value("theme_text_muted", "#a6adc8")
        cls.ACCENT_TEAL = settings.value("theme_accent_teal", "#4fd1c5")
        cls.ACCENT_BLUE = settings.value("theme_accent_blue", "#89b4fa")
        cls.ERROR = settings.value("theme_error", "#f38ba8")
        cls.SUCCESS = settings.value("theme_success", "#a6e3a1")
        cls.ICON_COLOR = settings.value("theme_icon_color", "#cdd6f4") # 🚀 NEW


class ThemeFonts:
    @staticmethod
    def ui_font(size=10, bold=False):
        font = QFont("Segoe UI", size)
        if bold: font.setBold(True)
        return font

    @staticmethod
    def code_font(size=12):
        return QFont("Consolas", size)


class ThemeIcons:
    @staticmethod
    def get_icon(icon_name, color_hex=None):
        # 🚀 CHANGED: Fallback to dynamic ICON_COLOR
        if color_hex is None:
            color_hex = ThemeColors.ICON_COLOR
            
        try:
            if hasattr(sys, '_MEIPASS'):
                icon_dir = os.path.join(sys._MEIPASS, "codesaver_icons")
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                icon_dir = os.path.join(base_dir, "codesaver_icons")
                
            icon_path = os.path.join(icon_dir, icon_name)
            if not os.path.exists(icon_path): 
                return QIcon()
                
            icon = QIcon(icon_path)
            new_icon = QIcon()
            
            for size in [16, 24, 32, 48, 64]:
                pixmap = icon.pixmap(size, size)
                if not pixmap.isNull():
                    painter = QPainter(pixmap)
                    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
                    painter.fillRect(pixmap.rect(), QColor(color_hex))
                    painter.end()
                    new_icon.addPixmap(pixmap)
                    
            return new_icon if not new_icon.isNull() else icon
        except Exception:
            return QIcon()


class ThemeManager:
    @staticmethod
    def get_global_stylesheet():
        ThemeColors.load_from_settings() 
        
        return f"""
        QWidget {{
            background-color: {ThemeColors.BG_BASE};
            color: {ThemeColors.TEXT_MAIN};
            font-family: "Segoe UI";
            font-size: 13px;
        }}

        QPushButton {{
            background-color: {ThemeColors.BG_PANEL};
            color: {ThemeColors.TEXT_MAIN};
            border: 1px solid {ThemeColors.BORDER_DEFAULT};
            border-radius: 6px;
            padding: 6px 12px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {ThemeColors.BORDER_ACTIVE};
            border: 1px solid {ThemeColors.ACCENT_BLUE};
        }}
        QPushButton:pressed {{
            background-color: {ThemeColors.ACCENT_BLUE};
            color: {ThemeColors.BG_INPUT};
        }}
        QPushButton:disabled {{
            background-color: transparent;
            color: {ThemeColors.TEXT_DISABLED};
            border: 1px dashed {ThemeColors.BORDER_DEFAULT};
        }}

        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {ThemeColors.BG_INPUT};
            color: {ThemeColors.TEXT_MAIN};
            border: 1px solid {ThemeColors.BORDER_DEFAULT};
            border-radius: 6px;
            padding: 6px;
            selection-background-color: rgba(137, 180, 250, 0.3);
        }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 1px solid {ThemeColors.ACCENT_TEAL};
        }}

        QListWidget, QTreeWidget {{
            background-color: {ThemeColors.BG_INPUT};
            border: 1px solid {ThemeColors.BORDER_DEFAULT};
            border-radius: 6px;
            outline: none;
        }}
        QListWidget::item, QTreeWidget::item {{
            padding: 8px;
            border-radius: 4px;
        }}
        QListWidget::item:hover, QTreeWidget::item:hover {{
            background-color: rgba(255, 255, 255, 0.05);
        }}
        QListWidget::item:selected, QTreeWidget::item:selected {{
            background-color: rgba(79, 209, 197, 0.15);
            color: {ThemeColors.ACCENT_TEAL};
            border-left: 3px solid {ThemeColors.ACCENT_TEAL};
        }}

        QScrollBar:vertical {{
            border: none;
            background: transparent;
            width: 10px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {ThemeColors.BORDER_DEFAULT};
            border-radius: 5px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {ThemeColors.BORDER_ACTIVE};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}

        QScrollBar:horizontal {{
            border: none;
            background: transparent;
            height: 10px;
            margin: 0px;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {ThemeColors.BORDER_DEFAULT};
            border-radius: 5px;
            min-width: 30px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background-color: {ThemeColors.BORDER_ACTIVE};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}
        
        QTabWidget::pane {{
            border: 1px solid {ThemeColors.BORDER_DEFAULT};
            background-color: {ThemeColors.BG_BASE};
        }}
        QTabBar::tab {{
            background-color: {ThemeColors.BG_PANEL};
            color: {ThemeColors.TEXT_MUTED};
            border: 1px solid {ThemeColors.BORDER_DEFAULT};
            border-bottom: none;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            padding: 6px 15px;
            margin-right: 2px;
        }}
        QTabBar::tab:selected {{
            background-color: {ThemeColors.BG_BASE};
            color: {ThemeColors.ACCENT_TEAL};
            border-top: 2px solid {ThemeColors.ACCENT_TEAL};
        }}
        QTabBar::tab:hover:!selected {{
            background-color: {ThemeColors.BORDER_ACTIVE};
            color: {ThemeColors.TEXT_MAIN};
        }}
        """