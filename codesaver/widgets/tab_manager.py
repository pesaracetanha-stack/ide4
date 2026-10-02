# -*- coding: utf-8 -*-
# codesaver/widgets/tab_manager.py
import os
from PySide6.QtCore import QObject, Signal, Qt, QEvent
from PySide6.QtWidgets import QMessageBox, QTabBar

from .code_editor import CodeEditor
from .welcome_screen import WelcomeScreen
from .editor_tab import EditorTab  
from ..core.theme_manager import ThemeIcons, ThemeColors

class TabDict(dict):
    def __init__(self, tab_widget):
        super().__init__()
        self.tab_widget = tab_widget

    def __setitem__(self, key, value):
        if isinstance(value, int):
            widget = self.tab_widget.widget(value)
            if widget:
                super().__setitem__(key, widget)
        else:
            super().__setitem__(key, value)

    def __getitem__(self, key):
        widget = super().__getitem__(key)
        idx = self.tab_widget.indexOf(widget)
        if idx == -1:
            raise KeyError(key)
        return idx


class TabManager(QObject):
    """Orchestrator for managing IDE tabs, routing, and lifecycle"""
    tab_changed_signal = Signal(object)

    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.tab_widget = main_window.editor_tab_widget
        self.version_mgr = main_window.version_mgr
        
        self.mw.open_tabs = TabDict(self.tab_widget)
        
        self.tab_widget.tabCloseRequested.connect(self.close_editor_tab)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.tab_widget.tabBar().installEventFilter(self)

    def eventFilter(self, obj, event):
        try:
            if obj == self.tab_widget.tabBar() and event.type() == QEvent.Type.MouseButtonRelease:
                if event.button() == Qt.MouseButton.MiddleButton:
                    tab_index = self.tab_widget.tabBar().tabAt(event.pos())
                    if tab_index >= 0:
                        if self.tab_widget.tabText(tab_index) != "Home":
                            self.close_editor_tab(tab_index)
                        return True
            return super().eventFilter(obj, event)
        except RuntimeError:
            return False

    def add_empty_tab(self):
        tab_title = "Home"
        
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == tab_title:
                self.tab_widget.setCurrentIndex(i)
                # 🚀 FIX 2: Force focus on the Welcome Screen to bring it to front properly 
                # even if triggered from outside docks (like the Architecture map)
                widget = self.tab_widget.widget(i)
                if widget: widget.setFocus()
                return

        welcome = WelcomeScreen(self.mw)
        
        try:
            tab_icon = ThemeIcons.get_icon("wellcome_scr.svg", ThemeColors.ACCENT_GOLD)
            idx = self.tab_widget.addTab(welcome, tab_icon, tab_title)
        except Exception:
            idx = self.tab_widget.addTab(welcome, tab_title)
            
        self.tab_widget.setCurrentIndex(idx)
        
        tab_bar = self.tab_widget.tabBar()
        tab_bar.setTabButton(idx, QTabBar.ButtonPosition.RightSide, None)
        tab_bar.setTabButton(idx, QTabBar.ButtonPosition.LeftSide, None)

        self.mw.current_editor_tab = None
        if hasattr(self.mw, 'address_bar'):
            self.mw.address_bar.clear()
        if hasattr(self.mw, 'history_dock'):
            self.mw.history_dock.set_current_file(None)

    def _remove_welcome_screen(self):
        tab_title = "Home"
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == tab_title:
                self.tab_widget.removeTab(i)
                break

    def open_file_in_tab(self, file_path):
        abs_path = os.path.abspath(file_path)
        if abs_path in self.mw.open_tabs:
            idx = self.mw.open_tabs[abs_path]
            self.tab_widget.setCurrentIndex(idx)
            
            widget = self.tab_widget.widget(idx)
            if isinstance(widget, EditorTab):
                widget.reload_content_if_changed()
            return
        
        try:
            tab = EditorTab(abs_path, self.version_mgr, self.tab_widget)
            tab.saved.connect(self.mw._on_file_saved)
            
            idx = self.tab_widget.addTab(tab, os.path.basename(abs_path))
            
            self._remove_welcome_screen()
            
            self.tab_widget.setCurrentIndex(idx)
            self.mw.open_tabs[abs_path] = idx
            
            if hasattr(tab.editor, 'cursorInfoChanged') and hasattr(self.mw, '_update_editor_status'):
                tab.editor.cursorInfoChanged.connect(self.mw._update_editor_status)
            if hasattr(tab.editor, 'update_cursor_info'):
                tab.editor.update_cursor_info()
                
            if hasattr(self.mw, 'history_dock') and self.mw.history_dock:
                self.mw.history_dock.set_current_file(abs_path)
                self.mw.history_dock.load_versions(self.version_mgr.get_versions(abs_path))
        except Exception as e:
            QMessageBox.critical(self.mw, "Error opening file", f"Could not open file:\n{str(e)}")

    def close_editor_tab(self, index, auto_add=True):
        if self.tab_widget.tabText(index) == "Home":
            return True
            
        widget = self.tab_widget.widget(index)
        if isinstance(widget, EditorTab):
            if widget.is_modified:
                reply = QMessageBox.question(self.mw, "Unsaved Changes", "Do you want to close the tab without saving?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply != QMessageBox.StandardButton.Yes: return False
            file_path = widget.file_path
            if file_path in self.mw.open_tabs: 
                del self.mw.open_tabs[file_path]
        
        self.tab_widget.removeTab(index)
        if widget: 
            widget.deleteLater()
        
        if auto_add and self.tab_widget.count() == 0: 
            self.add_empty_tab()
        return True

    def _on_tab_changed(self, index):
        widget = self.tab_widget.widget(index)
        if isinstance(widget, EditorTab):
            self.mw.current_editor_tab = widget
            rel = os.path.relpath(widget.file_path, self.mw.project_root) if self.mw.project_root else widget.file_path
            if hasattr(self.mw, 'address_bar'):
                self.mw.address_bar.setText(rel)
            if hasattr(self.mw, 'history_dock') and self.mw.history_dock:
                self.mw.history_dock.set_current_file(widget.file_path)
                self.mw.history_dock.load_versions(self.version_mgr.get_versions(widget.file_path))
        else:
            self.mw.current_editor_tab = None
            if hasattr(self.mw, 'address_bar'):
                self.mw.address_bar.clear()
            if hasattr(self.mw, 'history_dock') and self.mw.history_dock:
                self.mw.history_dock.set_current_file(None)
        self.tab_changed_signal.emit(self.mw.current_editor_tab)

    def save_current_file(self):
        if self.mw.current_editor_tab and hasattr(self.mw.current_editor_tab, 'save_content'):
            self.mw.current_editor_tab.save_content()
        else:
            current_widget = self.tab_widget.currentWidget()
            if current_widget and not isinstance(current_widget, EditorTab) and not isinstance(current_widget, WelcomeScreen):
                editor = current_widget.findChild(CodeEditor)
                if editor:
                    rel_path = getattr(self.mw, 'address_bar').text().strip() if hasattr(self.mw, 'address_bar') else ""
                    if not rel_path or not self.mw.project_root:
                        QMessageBox.warning(self.mw, "Unknown Path", "Please enter the file path in the Address Bar first to save it.")
                        return
                    
                    abs_path = os.path.join(self.mw.project_root, rel_path)
                    content = editor.toPlainText() if hasattr(editor, 'toPlainText') else ""
                    
                    try:
                        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                        with open(abs_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        if hasattr(self.mw.project_mgr, 'tree_refresh_needed'):
                            self.mw.project_mgr.tree_refresh_needed.emit()
                        
                        idx = self.tab_widget.indexOf(current_widget)
                        self.tab_widget.removeTab(idx)
                        current_widget.deleteLater()
                        
                        self.open_file_in_tab(abs_path)
                        if hasattr(self.mw, 'status_label'):
                            self.mw.status_label.setText(f"File created and saved successfully: {rel_path}")
                        
                    except Exception as e:
                        QMessageBox.critical(self.mw, "Error", f"Failed to save file:\n{e}")