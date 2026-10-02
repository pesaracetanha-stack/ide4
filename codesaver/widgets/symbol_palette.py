# -*- coding: utf-8 -*-
# codesaver/widgets/symbol_palette.py
import re
import os
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QLabel
from PySide6.QtCore import Signal, Qt, QEvent

from ..core.theme_manager import ThemeColors

class SymbolPalette(QFrame):
    symbol_selected = Signal(int)
    close_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)
        self.setObjectName("SymbolPalette")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.user_moved = False
        
        self.setFixedSize(500, 350)
        
        # 🚀 CHANGED: Using ThemeManager variables for the floating popup
        self.setStyleSheet(f"""
            #SymbolPalette {{
                background-color: {ThemeColors.BG_PANEL};
                border: 1px solid {ThemeColors.BORDER_ACTIVE};
                border-radius: 8px;
            }}
            QLabel {{
                color: {ThemeColors.TEXT_MUTED};
                font-size: 11px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Type to filter methods and classes... (Esc to close)")
        self.search_edit.textChanged.connect(self.filter_symbols)
        self.search_edit.returnPressed.connect(self.activate_selected)
        self.search_edit.installEventFilter(self)
        layout.addWidget(self.search_edit)
        
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.list_widget)
        
        self.status_lbl = QLabel("Use Up/Down arrows to navigate, Enter to select.")
        layout.addWidget(self.status_lbl)
        
        self.all_symbols = []

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, '_drag_start_pos'):
            self.move(self.pos() + event.position().toPoint() - self._drag_start_pos)
            self.user_moved = True
        super().mouseMoveEvent(event)

    def eventFilter(self, obj, event):
        if obj == self.search_edit and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Down:
                new_row = self.list_widget.currentRow() + 1
                if new_row < self.list_widget.count():
                    self.list_widget.setCurrentRow(new_row)
                return True
            elif event.key() == Qt.Key.Key_Up:
                new_row = self.list_widget.currentRow() - 1
                if new_row >= 0:
                    self.list_widget.setCurrentRow(new_row)
                return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide_palette()
        else:
            super().keyPressEvent(event)

    def load_symbols_from_text(self, text):
        self.list_widget.clear()
        self.all_symbols = []
        self.search_edit.clear()
        
        lines = text.split('\n')
        pattern = re.compile(r'^\s*(def\s+|class\s+|function\s+|async\s+def\s+)([a-zA-Z_][a-zA-Z0-9_]*)')
        
        for idx, line in enumerate(lines):
            match = pattern.search(line)
            if match:
                symbol_type = match.group(1).strip()
                symbol_name = match.group(2).strip()
                line_num = idx + 1
                
                display_text = f"[{symbol_type.upper()}]  {symbol_name}  (Line {line_num})"
                self.all_symbols.append((display_text, line_num))
        
        self.update_list(self.all_symbols)

    def update_list(self, symbols_list):
        self.list_widget.clear()
        for display_text, line_num in symbols_list:
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, line_num)
            self.list_widget.addItem(item)
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def filter_symbols(self, text):
        if not text:
            self.update_list(self.all_symbols)
            return
        filtered = [sym for sym in self.all_symbols if text.lower() in sym[0].lower()]
        self.update_list(filtered)

    def activate_selected(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            line_num = current_item.data(Qt.ItemDataRole.UserRole)
            self.symbol_selected.emit(line_num)
            self.hide_palette()

    def on_item_double_clicked(self, item):
        line_num = item.data(Qt.ItemDataRole.UserRole)
        self.symbol_selected.emit(line_num)
        self.hide_palette()

    def hide_palette(self):
        self.setVisible(False)
        self.close_requested.emit()