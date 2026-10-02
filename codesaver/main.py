# -*- coding: utf-8 -*-
# codesaver/main.py
import sys
import os

# DPI FIX: Forcing Qt to calculate exact scaling across multiple monitors before anything loads
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_SCALE_FACTOR"] = "1"

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--disable-direct-composition "     
    "--disable-gpu-compositing "        
    "--enable-software-rasterizer "     
    "--enable-webgl"                    
)

import base64
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QSplashScreen
from PySide6.QtCore import Qt, QSettings, QByteArray, QTimer
from PySide6.QtGui import QIcon, QPixmap

# Core Managers
from .core.config import ConfigManager
from .core.restore_points import RestorePointManager
from .core.version_history import VersionHistoryManager
from .core.project_manager import ProjectManager
from .core.git_manager import GitManager
from .core.splash_data import SPLASH_BASE64
from .core.plugin_manager import PluginManager
from .core.ai_injector import AIInjector
from .core.theme_manager import ThemeManager, ThemeColors 
from .widgets.actions.action_mixin import EditorActionsMixin

# UI & Dialogs
from .widgets.main_ui_builder import UIBuilder
from .widgets.tab_manager import TabManager


class MainWindow(QMainWindow, EditorActionsMixin):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Code Saver - IDE Master v4.0")
        self.resize(1250, 820)
        
        self.project_root = None
        self.current_project_file = None
        self.current_editor_tab = None
        self.open_tabs = {}
        self.path_to_item = {}

        self.config_mgr = ConfigManager()
        self.version_mgr = VersionHistoryManager()
        self.project_mgr = ProjectManager(self)
        self.git_mgr = GitManager(self)
        self.restore_mgr = None

        self.ui_builder = UIBuilder(self)
        self.ui_builder.build_phase1_core()
        self.tab_mgr = TabManager(self)
        self.ui_builder.build_phase2_menus()

        self._connect_signals()
        self._load_config()
        
        self.plugin_mgr = PluginManager(self)
        self.ai_injector = AIInjector(self)

        base_style = ThemeManager.get_global_stylesheet()
        menu_style = f"""
            QMenuBar {{
                background-color: transparent;
                color: {ThemeColors.TEXT_MAIN};
            }}
            QMenuBar::item:selected {{
                background-color: {ThemeColors.ACCENT_BLUE};
                color: #ffffff;
                border-radius: 4px;
            }}
            QMenu {{
                background-color: {ThemeColors.BG_PANEL};
                color: {ThemeColors.TEXT_MAIN};
                border: 1px solid {ThemeColors.BORDER_DEFAULT};
            }}
            QMenu::item:selected {{
                background-color: {ThemeColors.ACCENT_BLUE};
                color: #ffffff;
            }}
        """
        self.setStyleSheet(base_style + menu_style)
        
        if self.editor_tab_widget.count() == 0:
            self.tab_mgr.add_empty_tab()
            
        self._force_windows_taskbar_icon()

    def _force_windows_taskbar_icon(self):
        """Directly inject the icon into the Windows Taskbar using pywin32"""
        if sys.platform == 'win32':
            try:
                import win32gui
                import win32con
                from .core.resource_manager import ResourceManager
                
                icon_path = ResourceManager.get_path("app_icon.ico")
                if os.path.exists(icon_path):
                    self.setWindowIcon(QIcon(icon_path))
                    
                    hwnd = self.winId()
                    icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
                    hicon = win32gui.LoadImage(
                        0, icon_path, win32con.IMAGE_ICON, 0, 0, icon_flags
                    )
                    
                    win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_BIG, hicon)
                    win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_SMALL, hicon)
            except Exception as e:
                print(f"Win32 Icon Injection Failed: {e}")

    def _connect_signals(self):
        self.project_mgr.tree_refresh_needed.connect(self.tree.refresh_tree)
        self.project_mgr.directory_changed_signal.connect(lambda p: self.tree.refresh_tree())
        self.tree.file_opened.connect(self.tab_mgr.open_file_in_tab)
        
        self.chatbot_panel.context_fetch_requested.connect(self._provide_ai_context)
        
        if hasattr(self.terminal, 'error_detected'):
            self.terminal.error_detected.connect(self.chatbot_panel.handle_terminal_error)

    # =========================================================================
    # Project Lifecycle Management
    # =========================================================================
    def _load_project_env(self, path):
        for i in range(self.editor_tab_widget.count() - 1, -1, -1):
            if not self.tab_mgr.close_editor_tab(i, auto_add=False): return
        
        self.open_tabs.clear()
        self.project_mgr.set_project_root(path)
        self._add_to_recent(path)
        
        self.version_mgr.set_project_root(path)
        self.restore_mgr = RestorePointManager(path)
        self.global_search_overlay.set_project_root(path)
        self.terminal.change_working_directory(path)
        self.arch_map.set_project_root(path)
        
        self.tab_mgr.add_empty_tab()
        self._save_config()

    def _new_project(self):
        if self._prompt_close_project():
            if folder := QFileDialog.getExistingDirectory(self, "Select or Create New Project Folder"):
                self.current_project_file = None
                self._load_project_env(folder)

    def _open_project_folder(self):
        if self._prompt_close_project():
            if folder := QFileDialog.getExistingDirectory(self, "Select Project Folder"):
                self.current_project_file = None
                self._load_project_env(folder)

    def _close_project(self):
        if not self.project_root or not self._prompt_close_project(): return
        
        for i in range(self.editor_tab_widget.count() - 1, -1, -1):
            self.tab_mgr.close_editor_tab(i, auto_add=False)
        self.tab_mgr.add_empty_tab()
        
        self.project_root = self.current_project_file = None
        self.open_tabs.clear()
        self.tree.show_empty_tree()
        self.address_bar.clear()
        self.history_dock.set_current_file(None)
        self.global_search_overlay.setVisible(False)
        self.arch_map.set_project_root(None)
        self.setWindowTitle("Code Saver - IDE Master v4.0")
        self.status_label.setText("No project opened.")

    def _save_project(self):
        if not self.project_root: return
        self._save_all_modified_tabs()
        if self.current_project_file:
            success, msg = self.project_mgr.export_workspace(self.current_project_file, list(self.open_tabs.keys()))
            self.status_label.setText(msg)

    def _save_project_as(self):
        if not self.project_root: return
        self._save_all_modified_tabs()
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Project As", self.project_root, "CodeSaver Project (*.csprj)")
        if save_path:
            self.current_project_file = save_path
            success, msg = self.project_mgr.export_workspace(save_path, list(self.open_tabs.keys()))
            self.status_label.setText(msg)

    def _open_project_workspace(self):
        if not self._prompt_close_project(): return
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Project Workspace", "", "CodeSaver Project (*.csprj)")
        if file_path:
            dest_folder = QFileDialog.getExistingDirectory(self, "Select Folder to Extract Project")
            if not dest_folder: return
            success, result = self.project_mgr.extract_workspace(file_path, dest_folder)
            if success:
                self.current_project_file = file_path
                self._load_project_env(dest_folder)
                for rel_path in result.get("open_tabs", []):
                    if os.path.exists(abs_path := os.path.join(dest_folder, rel_path)): 
                        self.tab_mgr.open_file_in_tab(abs_path)
                self.status_label.setText("Project loaded successfully.")
            else:
                QMessageBox.critical(self, "Error", result)

    def _prompt_close_project(self):
        if not self.project_root: return True
        reply = QMessageBox.question(self, "Close Project", "Do you want to close the current project?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No: return False
        
        reply_save = QMessageBox.question(self, "Save Project", "Do you want to save your changes before closing?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply_save == QMessageBox.StandardButton.Yes: self._save_project()
        return True

    def _save_all_modified_tabs(self):
        for i in range(self.editor_tab_widget.count()):
            if hasattr(widget := self.editor_tab_widget.widget(i), 'is_modified') and widget.is_modified:
                widget.save_content()

    def closeEvent(self, event):
        has_unsaved_changes = False
        for i in range(self.editor_tab_widget.count()):
            widget = self.editor_tab_widget.widget(i)
            if hasattr(widget, 'is_modified') and widget.is_modified:
                has_unsaved_changes = True
                break

        if not has_unsaved_changes:
            if self.project_root and self.current_project_file:
                self._save_project()
            event.accept()
            return

        msg = QMessageBox(self)
        msg.setWindowTitle("Unsaved Changes")
        msg.setText("Do you want to close the project without saving changes?")
        
        btn_yes = msg.addButton("Yes", QMessageBox.ButtonRole.YesRole)
        btn_no = msg.addButton("No", QMessageBox.ButtonRole.NoRole)
        msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        msg.setDefaultButton(btn_no)
        msg.exec()

        if msg.clickedButton() == btn_yes:
            event.accept()
        elif msg.clickedButton() == btn_no:
            self._save_all_modified_tabs()
            if self.project_root and self.current_project_file:
                self._save_project()
            event.accept()
        else:
            event.ignore()

    def _provide_ai_context(self, context_dict):
        context_dict['tree'] = self.project_mgr.get_tree_structure()
        if self.current_editor_tab and hasattr(self.current_editor_tab, 'editor'):
            context_dict['active_file_content'] = self.current_editor_tab.editor.toPlainText()
            context_dict['active_file_name'] = os.path.basename(getattr(self.current_editor_tab, 'file_path', 'Unknown'))
        else:
            context_dict['active_file_content'] = ""
            context_dict['active_file_name'] = "No Active File"

    def _load_config(self):
        self.config_mgr.load()
        self.address_bar.setPlaceholderText("Relative file path (e.g., src/main.py) and press Enter")
        if self.config_mgr.project_root and os.path.isdir(self.config_mgr.project_root):
            self.project_mgr.hidden_folders = set(self.config_mgr.hidden_folders)
            self.tree.show_empty_tree()
        self._update_recent_menu()

    def _save_config(self):
        if self.project_root:
            self.config_mgr.project_root = self.project_root
            self.config_mgr.hidden_folders = list(self.project_mgr.hidden_folders)
            self.config_mgr.save()

    def _add_to_recent(self, path):
        settings = QSettings("HPR", "CodeSaver")
        recent = settings.value("recent_projects", [])
        recent = [] if not isinstance(recent, list) else recent
        if path in recent: recent.remove(path)
        recent.insert(0, path)
        settings.setValue("recent_projects", recent[:10])
        self._update_recent_menu()

    def _update_recent_menu(self):
        self.ui_builder.build_recent_menu()


def main():
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtCore import Qt
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    app.setStyleSheet(ThemeManager.get_global_stylesheet())
    
    splash_pixmap = QPixmap()
    splash_pixmap.loadFromData(QByteArray(base64.b64decode(SPLASH_BASE64)))
    splash = QSplashScreen(splash_pixmap, Qt.WindowType.WindowStaysOnTopHint)
    splash.show()
    app.processEvents()

    temp_config = ConfigManager()
    temp_config.load()
    
    window = MainWindow()

    def show_main():
        window.show()
        splash.finish(window)

    QTimer.singleShot(2000, show_main)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()