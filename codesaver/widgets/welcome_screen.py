# -*- coding: utf-8 -*-
# codesaver/widgets/welcome_screen.py
import os
import sys
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QListWidget, QListWidgetItem, 
                               QFrame, QGridLayout, QSizePolicy, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QSettings, QSize
from PySide6.QtGui import QCursor, QIcon, QPixmap, QPainter, QColor, QFont

def _get_safe_icon_path(filename):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, "codesaver_icons", filename)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "codesaver_icons", filename)

def load_colored_icon(filepath, color="#007AAC"):
    if not os.path.exists(filepath):
        return QIcon()
    
    icon = QIcon(filepath)
    new_icon = QIcon()
    for size in [16, 24, 32, 48, 64]:
        pixmap = icon.pixmap(size, size)
        if not pixmap.isNull():
            painter = QPainter(pixmap)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(pixmap.rect(), QColor(color))
            painter.end()
            new_icon.addPixmap(pixmap)
            
    return new_icon if not new_icon.isNull() else icon


class WelcomeScreen(QWidget):
    """Fully Responsive, English-only Glassmorphism Start Dashboard"""
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
            
        theme = QSettings("GitiArts", "CodeSaver_Theme")
        self.icon_color = theme.value("icon_color", "#4fd1c5")
            
        self.setup_ui()
        self.load_recent_projects()

    def setup_ui(self):
        self.setStyleSheet("background-color: #1a1c23;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # استفاده از حاشیه‌های منعطف به جای اعداد ثابت بزرگ
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)
        
        # ==============================================================
        # Hero Section (Title & Subtitle)
        # ==============================================================
        hero_layout = QVBoxLayout()
        hero_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_layout.setSpacing(5)
        
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        home_icon_lbl = QLabel()
        home_icon_path = _get_safe_icon_path("wellcome_scr.svg")
        home_pixmap = load_colored_icon(home_icon_path, "#ffd700").pixmap(48, 48)
        home_icon_lbl.setPixmap(home_pixmap)
        
        lbl_title = QLabel("CodeSaver IDE")
        lbl_title.setFont(QFont("Segoe UI", 42, QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: #ffd700; letter-spacing: 2px;") 
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_layout.addWidget(home_icon_lbl)
        title_layout.addWidget(lbl_title)
        
        lbl_subtitle = QLabel("Smarter, faster, and more enjoyable coding with AI Assistant")
        lbl_subtitle.setFont(QFont("Consolas", 14))
        lbl_subtitle.setStyleSheet("color: #4fd1c5; margin-bottom: 15px;") 
        lbl_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        hero_layout.addLayout(title_layout)
        hero_layout.addWidget(lbl_subtitle)
        
        main_layout.addLayout(hero_layout)

        # ==============================================================
        # Responsive Content Section
        # ==============================================================
        content_layout = QHBoxLayout()
        content_layout.setSpacing(30)
        
        # --- 1. Quick Actions Panel ---
        action_panel = self.create_glass_panel()
        action_layout = QVBoxLayout(action_panel)
        action_layout.setSpacing(15)
        
        lbl_start = QLabel("🚀 Quick Actions")
        lbl_start.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        lbl_start.setStyleSheet("color: #cdd6f4; border: none; background: transparent;")
        action_layout.addWidget(lbl_start)

        grid = QGridLayout()
        grid.setSpacing(12)

        btn_new_proj = self._create_action_button("New Project", "Create blank folder", "new_folder.svg")
        btn_new_proj.clicked.connect(self.mw._new_project)
        grid.addWidget(btn_new_proj, 0, 0)

        btn_open_folder = self._create_action_button("Open Folder", "Load project code", "open_folder.svg")
        btn_open_folder.clicked.connect(self.mw._open_project_folder)
        grid.addWidget(btn_open_folder, 0, 1)

        btn_open_ws = self._create_action_button("Open Workspace", "Extract .csprj files", "workspace.svg")
        btn_open_ws.clicked.connect(self.mw._open_project_workspace)
        grid.addWidget(btn_open_ws, 1, 0)

        btn_new_file = self._create_action_button("New File", "Temp new file", "new_file.svg")
        btn_new_file.clicked.connect(self.mw.project_mgr.create_new_file)
        grid.addWidget(btn_new_file, 1, 1)

        btn_ai = self._create_action_button("AI Assistant", "Smart chat panel", "chat_bot.svg")
        btn_ai.clicked.connect(lambda: self.mw.btn_ai.setChecked(True) if hasattr(self.mw, 'btn_ai') else None)
        grid.addWidget(btn_ai, 2, 0)

        btn_settings = self._create_action_button("Preferences", "Customize UI & fonts", "general_settings.svg")
        btn_settings.clicked.connect(self.mw._open_preferences)
        grid.addWidget(btn_settings, 2, 1)

        action_layout.addLayout(grid)
        action_layout.addStretch()

        # Tip Section
        tip_frame = QFrame()
        tip_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        tip_frame.setStyleSheet("""
            QFrame { 
                background-color: rgba(255, 255, 255, 0.03); 
                border-radius: 8px; 
                border: 1px solid rgba(255, 255, 255, 0.05); 
                border-left: 4px solid #a6e3a1; 
            }
        """)
        tip_layout = QVBoxLayout(tip_frame)
        tip_layout.setContentsMargins(15, 10, 15, 10)
        
        tip_title_layout = QHBoxLayout()
        tip_icon_lbl = QLabel()
        tip_pixmap = load_colored_icon(_get_safe_icon_path("tip.svg"), "#f9e2af").pixmap(18, 18)
        tip_icon_lbl.setPixmap(tip_pixmap)
        tip_icon_lbl.setStyleSheet("background: transparent; border: none;")
        
        lbl_tip_title = QLabel("Did you know?")
        lbl_tip_title.setStyleSheet("color: #f9e2af; font-size: 13px; font-weight: bold; border: none; background: transparent;")
        
        tip_title_layout.addWidget(tip_icon_lbl)
        tip_title_layout.addWidget(lbl_tip_title)
        tip_title_layout.addStretch()
        
        lbl_tip_desc = QLabel("By pressing <b>Ctrl+Shift+P</b> you can open the Command Palette to execute anything without a mouse!")
        lbl_tip_desc.setStyleSheet("color: #cdd6f4; font-size: 12px; line-height: 1.4; border: none; background: transparent; margin-top: 5px;")
        lbl_tip_desc.setWordWrap(True)
        
        tip_layout.addLayout(tip_title_layout)
        tip_layout.addWidget(lbl_tip_desc)
        action_layout.addWidget(tip_frame)
        
        # --- 2. Recent Projects Panel ---
        recent_panel = self.create_glass_panel()
        recent_layout = QVBoxLayout(recent_panel)
        recent_layout.setSpacing(15)
        
        recent_title_layout = QHBoxLayout()
        recent_icon_lbl = QLabel()
        recent_pixmap = load_colored_icon(_get_safe_icon_path("open_recent.svg"), self.icon_color).pixmap(24, 24)
        recent_icon_lbl.setPixmap(recent_pixmap)
        recent_icon_lbl.setStyleSheet("background: transparent; border: none;")
        
        lbl_recent = QLabel("Recent Projects")
        lbl_recent.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        lbl_recent.setStyleSheet("color: #cdd6f4; border: none; background: transparent;")
        
        recent_title_layout.addWidget(recent_icon_lbl)
        recent_title_layout.addWidget(lbl_recent)
        recent_title_layout.addStretch()
        
        recent_layout.addLayout(recent_title_layout)
        
        self.recent_list = QListWidget()
        self.recent_list.setIconSize(QSize(22, 22))
        self.recent_list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                color: #a6accd;
                padding: 10px;
                border-radius: 6px;
                margin-bottom: 5px;
                font-family: 'Segoe UI';
                font-size: 13px;
                border: 1px solid transparent;
            }
            QListWidget::item:hover {
                background-color: rgba(79, 209, 197, 0.15);
                border: 1px solid rgba(79, 209, 197, 0.3);
                color: #4fd1c5;
            }
        """)
        self.recent_list.setCursor(Qt.CursorShape.PointingHandCursor)
        self.recent_list.itemClicked.connect(self.on_recent_clicked)
        recent_layout.addWidget(self.recent_list)

        # تقسیم فضا با نسبت 6 به 4 (واکنش‌گرا)
        content_layout.addWidget(action_panel, stretch=6)
        content_layout.addWidget(recent_panel, stretch=4)
            
        main_layout.addLayout(content_layout)

    def create_glass_panel(self):
        """Creates a fully responsive translucent panel with Glassmorphism effects"""
        panel = QFrame()
        # اجازه می‌دهیم پنل‌ها آزادانه تغییر اندازه دهند
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # فقط یک حداقل عرض و ارتفاع تعیین می‌کنیم تا از حد مشخصی جمع‌تر نشوند
        panel.setMinimumSize(300, 300)
        
        panel.setStyleSheet("""
            QFrame {
                background-color: rgba(13, 25, 48, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
            }
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 8)
        panel.setGraphicsEffect(shadow)
        return panel

    def _create_action_button(self, title, subtitle, icon_filename):
        btn = QPushButton()
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        # دکمه‌ها منعطف هستند تا در رزولوشن‌های مختلف کش بیایند
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        btn.setMinimumHeight(70)
        
        btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.03);
                border-radius: 8px;
                text-align: left;
                border: 1px solid rgba(255, 255, 255, 0.05);
            }
            QPushButton:hover {
                background-color: rgba(79, 209, 197, 0.15);
                border: 1px solid rgba(79, 209, 197, 0.3);
            }
        """)
        
        layout = QHBoxLayout(btn)
        layout.setContentsMargins(12, 8, 12, 8)
        
        icon_lbl = QLabel()
        icon_path = _get_safe_icon_path(icon_filename)
        icon_pixmap = load_colored_icon(icon_path, self.icon_color).pixmap(28, 28)
        
        icon_lbl.setPixmap(icon_pixmap)
        icon_lbl.setFixedSize(32, 32)
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("color: #cdd6f4; font-size: 14px; font-weight: bold; border: none; background: transparent;")
        text_layout.addWidget(lbl_t)
        
        lbl_s = QLabel(subtitle)
        lbl_s.setStyleSheet("color: #a6adc8; font-size: 11px; border: none; background: transparent;")
        lbl_s.setWordWrap(True) # اگر مانیتور خیلی کوچک بود، متن توضیحات به خط بعد برود
        text_layout.addWidget(lbl_s)
        
        layout.addWidget(icon_lbl)
        layout.addLayout(text_layout)
        layout.addStretch()
        
        return btn

    def load_recent_projects(self):
        self.recent_list.clear()
        settings = QSettings("HPR", "CodeSaver")
        recent = settings.value("recent_projects", [])
        recent = [] if not isinstance(recent, list) else recent
        
        folder_icon_path = _get_safe_icon_path("opened_folder.svg")
        folder_icon = load_colored_icon(folder_icon_path, "#ffd700") 
        
        added_count = 0
        for path in recent[:10]:
            if os.path.exists(path):
                item = QListWidgetItem(f" {os.path.basename(path)}\n  {path}")
                item.setIcon(folder_icon)
                item.setData(Qt.ItemDataRole.UserRole, path) 
                self.recent_list.addItem(item)
                added_count += 1
                
        if added_count == 0:
            empty_item = QListWidgetItem("No recent projects found. Open a folder!")
            empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
            empty_item.setForeground(QColor("#6e738d"))
            self.recent_list.addItem(empty_item)

    def on_recent_clicked(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path and hasattr(self.mw, '_load_project_env'):
            self.mw._load_project_env(path)