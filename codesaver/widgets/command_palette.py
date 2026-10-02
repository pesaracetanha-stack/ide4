# -*- coding: utf-8 -*-
# codesaver/widgets/command_palette.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem
from PySide6.QtCore import Qt, QEvent, QTimer
from PySide6.QtGui import QAction

from ..core.theme_manager import ThemeColors

class CommandPalette(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.mw = main_window
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.hide()

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        self.container = QWidget()
        self.container.setObjectName("CmdContainer")
        self.container.setStyleSheet(f"""
            #CmdContainer {{
                background-color: {ThemeColors.BG_PANEL};
                border: 1px solid {ThemeColors.ACCENT_BLUE};
                border-radius: 8px;
            }}
        """)
        
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)

        self.search_box = QLineEdit()
        self.search_box.setStyleSheet("border: none; border-bottom: 1px solid #45475a; padding: 12px; font-size: 15px;")
        self.search_box.textChanged.connect(self.filter_commands)
        self.search_box.returnPressed.connect(self.execute_selected)
        self.search_box.installEventFilter(self)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("border: none; padding: 5px;")
        self.list_widget.itemClicked.connect(self.execute_item)
        self.list_widget.installEventFilter(self)

        self.container_layout.addWidget(self.search_box)
        self.container_layout.addWidget(self.list_widget)
        self.layout.addWidget(self.container)

        self.all_actions = []
        self.mw.installEventFilter(self)

    def gather_actions(self):
        self.all_actions = []
        
        def scan_menu(menu, path=""):
            for action in menu.actions():
                if action.isSeparator(): 
                    continue
                if action.menu():
                    new_path = f"{path} > {action.text().replace('&', '')}" if path else action.text().replace('&', '')
                    scan_menu(action.menu(), new_path)
                else:
                    self.all_actions.append((action, path))

        menubar = self.mw.menuBar()
        scan_menu(menubar)

    def update_position(self):
        w = 600
        h = 450
        x = (self.mw.width() - w) // 2
        y = 50
        
        if hasattr(self.mw, 'global_search_bar') and hasattr(self.mw.global_search_bar, 'search_input'):
            target_widget = self.mw.global_search_bar.search_input
            pos = target_widget.mapTo(self.mw, target_widget.rect().topLeft())
            
            w = target_widget.width() + 20  
            x = pos.x() - 10
            y = pos.y() - 10

        self.resize(w, h)
        self.move(x, y)

    def show_palette(self):
        self.gather_actions()
        self.search_box.clear()
        self.filter_commands("")
        
        self.search_box.setPlaceholderText("Search for a command, plugin, or tool...")
        self.search_box.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        self.update_position()
        self.raise_()  
        self.show()
        self.search_box.setFocus()

    def filter_commands(self, text):
        self.list_widget.clear()
        text = text.lower()
        
        for action, path in self.all_actions:
            action_text = action.text().replace("&", "")
            full_text = f"{path} > {action_text}" if path else action_text
            
            if not text or text in full_text.lower():
                item = QListWidgetItem(full_text)
                if not action.icon().isNull():
                    item.setIcon(action.icon())
                    
                item.setData(Qt.ItemDataRole.UserRole, action)
                self.list_widget.addItem(item)
        
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def execute_selected(self):
        if self.list_widget.count() > 0:
            item = self.list_widget.currentItem() or self.list_widget.item(0)
            self.execute_item(item)

    def execute_item(self, item):
        action = item.data(Qt.ItemDataRole.UserRole)
        self.hide()
        if action and action.isEnabled():
            action.trigger()

    def eventFilter(self, obj, event):
        if obj == self.mw and event.type() in (QEvent.Type.Resize, QEvent.Type.WindowStateChange):
            if self.isVisible():
                QTimer.singleShot(10, self.update_position)
            return False
            
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                self.hide()
                return True
            elif event.key() == Qt.Key.Key_Down and obj == self.search_box:
                self.list_widget.setFocus()
                if self.list_widget.currentRow() < 0 and self.list_widget.count() > 0:
                    self.list_widget.setCurrentRow(0)
                return True
            elif event.key() == Qt.Key.Key_Up and obj == self.list_widget:
                if self.list_widget.currentRow() == 0:
                    self.search_box.setFocus()
                    return True
                    
        elif event.type() == QEvent.Type.WindowDeactivate or event.type() == QEvent.Type.FocusOut:
            QTimer.singleShot(100, self._check_focus)
            
        return super().eventFilter(obj, event)
        
    def _check_focus(self):
        if not self.search_box.hasFocus() and not self.list_widget.hasFocus():
            self.hide()