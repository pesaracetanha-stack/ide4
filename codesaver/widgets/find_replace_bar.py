# -*- coding: utf-8 -*-
# codesaver/widgets/find_replace_bar.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QFrame
from PySide6.QtCore import Signal, Qt

from ..core.theme_manager import ThemeColors

class FindReplaceBar(QFrame):
    find_next = Signal(str, bool)
    find_prev = Signal(str, bool)
    replace_current = Signal(str, str, bool)
    replace_all = Signal(str, str, bool)
    closed = Signal()
    search_updated = Signal(str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)
        self.setObjectName("FindBar")
        
        self.user_moved = False 
        
        self.setStyleSheet(f"""
            #FindBar {{
                background-color: {ThemeColors.BG_PANEL};
                border: 1px solid {ThemeColors.BORDER_ACTIVE};
                border-radius: 6px;
            }}
            QPushButton {{
                background-color: transparent;
                border: none;
                padding: 4px;
                border-radius: 4px;
            }}
            QPushButton:hover {{ background-color: {ThemeColors.BORDER_ACTIVE}; }}
            QPushButton:checked {{ background-color: {ThemeColors.ACCENT_BLUE}; color: {ThemeColors.BG_BASE}; }}
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(5)

        row_find = QHBoxLayout()
        row_find.setContentsMargins(0, 0, 0, 0)
        row_find.setSpacing(4)

        self.btn_toggle = QPushButton("⯈")
        self.btn_toggle.setFixedSize(28, 28)
        self.btn_toggle.setToolTip("Toggle Replace")
        self.btn_toggle.clicked.connect(self.toggle_replace)
        row_find.addWidget(self.btn_toggle)

        self.find_edit = QLineEdit()
        self.find_edit.setPlaceholderText("🔍 Find")
        self.find_edit.textChanged.connect(self._on_text_changed)
        row_find.addWidget(self.find_edit)

        self.count_label = QLabel("No results")
        row_find.addWidget(self.count_label)

        self.btn_next = QPushButton("↓")
        self.btn_next.setFixedSize(28, 28)
        self.btn_next.setToolTip("Next Match")
        
        self.btn_prev = QPushButton("↑")
        self.btn_prev.setFixedSize(28, 28)
        self.btn_prev.setToolTip("Previous Match")

        self.btn_case = QPushButton("Aa")
        self.btn_case.setCheckable(True)
        self.btn_case.setFixedSize(28, 28)
        self.btn_case.setToolTip("Match Case")
        self.btn_case.toggled.connect(self._on_text_changed)

        self.btn_close = QPushButton("✕")
        self.btn_close.setObjectName("closeBtn")
        self.btn_close.setFixedSize(28, 28)
        self.btn_close.setStyleSheet(f"QPushButton:hover {{ background-color: {ThemeColors.ERROR}; color: white; }}")
        self.btn_close.setToolTip("Close (Esc)")

        row_find.addWidget(self.btn_next)
        row_find.addWidget(self.btn_prev)
        row_find.addWidget(self.btn_case)
        row_find.addWidget(self.btn_close)

        main_layout.addLayout(row_find)

        self.replace_widget = QWidget()
        row_replace = QHBoxLayout(self.replace_widget)
        row_replace.setContentsMargins(32, 0, 0, 0)
        row_replace.setSpacing(4)

        self.replace_edit = QLineEdit()
        self.replace_edit.setPlaceholderText("Replace")
        row_replace.addWidget(self.replace_edit)

        self.btn_replace = QPushButton("Replace")
        self.btn_replace_all = QPushButton("All")

        row_replace.addWidget(self.btn_replace)
        row_replace.addWidget(self.btn_replace_all)

        main_layout.addWidget(self.replace_widget)
        self.replace_widget.setVisible(False)

        self.btn_next.clicked.connect(self._on_next)
        self.btn_prev.clicked.connect(self._on_prev)
        self.btn_replace.clicked.connect(self._on_replace)
        self.btn_replace_all.clicked.connect(self._on_replace_all)
        self.btn_close.clicked.connect(self.hide_bar)
        self.find_edit.returnPressed.connect(self._on_next)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, '_drag_start_pos'):
            self.move(self.pos() + event.position().toPoint() - self._drag_start_pos)
            self.user_moved = True 
        super().mouseMoveEvent(event)

    def toggle_replace(self):
        is_visible = self.replace_widget.isVisible()
        self.replace_widget.setVisible(not is_visible)
        self.btn_toggle.setText("⯆" if not is_visible else "⯈")
        self.adjustSize()

    def _on_text_changed(self):
        text = self.find_edit.text()
        self.search_updated.emit(text, self.btn_case.isChecked())

    def _on_next(self):
        if self.find_edit.text():
            self.find_next.emit(self.find_edit.text(), self.btn_case.isChecked())

    def _on_prev(self):
        if self.find_edit.text():
            self.find_prev.emit(self.find_edit.text(), self.btn_case.isChecked())

    def _on_replace(self):
        if self.find_edit.text():
            self.replace_current.emit(self.find_edit.text(), self.replace_edit.text(), self.btn_case.isChecked())

    def _on_replace_all(self):
        if self.find_edit.text():
            self.replace_all.emit(self.find_edit.text(), self.replace_edit.text(), self.btn_case.isChecked())

    def hide_bar(self):
        self.setVisible(False)
        self.search_updated.emit("", False)
        self.closed.emit()