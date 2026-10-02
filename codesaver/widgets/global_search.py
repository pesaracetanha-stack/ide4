# -*- coding: utf-8 -*-
# codesaver/widgets/global_search.py
import os
import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
                               QPushButton, QLabel, QFrame, QScrollArea, QApplication)
from PySide6.QtCore import Signal, Qt, QThread

# 🚀 NEW: Import central theme colors
from ..core.theme_manager import ThemeColors

def is_local_text_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    valid_exts = {'.py', '.txt', '.html', '.css', '.js', '.json', '.xml', '.md', '.vue', '.cpp', '.h', '.c'}
    return ext in valid_exts or ext == ''

class SearchWorker(QThread):
    match_found = Signal(str)
    finished_search = Signal(int)

    def __init__(self, project_root, text):
        super().__init__()
        self.project_root = project_root
        self.text = text.lower()
        self._is_running = True

    def run(self):
        if not self.project_root or not self.text:
            self.finished_search.emit(0)
            return
        
        ignore_dirs = {'.codesaver', '.git', 'node_modules', 'venv', '.venv', '__pycache__', 'dist', 'build'}
        matched_count = 0

        for root_dir, dirs, files in os.walk(self.project_root):
            if not self._is_running: break
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for file in files:
                if not self._is_running: break
                file_path = os.path.join(root_dir, file)
                if not is_local_text_file(file_path):
                    continue
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            if not self._is_running: break
                            if self.text in line.lower():
                                self.match_found.emit(file_path)
                                matched_count += 1
                                break
                except PermissionError as e:
                    logging.error(f"Access error: Cannot read file for global search ({file_path}): {e}")
                except Exception as e:
                    logging.error(f"System error during file scan and search ({file_path}): {e}")
                    
        self.finished_search.emit(matched_count)

    def stop(self):
        self._is_running = False

class FileCard(QFrame):
    clicked_card = Signal(object, str)

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setFixedSize(90, 110)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("FileCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True) 

        ext = os.path.splitext(file_path)[1].lower() or ".txt"
        name = os.path.basename(file_path)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        self.icon_lbl = QLabel(ext)
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 🚀 CHANGED: Using ThemeColors for the file badge
        self.icon_lbl.setStyleSheet(f"""
            QLabel {{
                color: {ThemeColors.ACCENT_TEAL}; font-weight: bold; font-size: 14px; 
                border: 2px solid {ThemeColors.BORDER_ACTIVE}; border-radius: 6px; 
                border-top-right-radius: 15px; background-color: {ThemeColors.BG_PANEL};
            }}
        """)

        self.name_lbl = QLabel(name)
        self.name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_lbl.setStyleSheet(f"color: {ThemeColors.TEXT_MAIN}; font-size: 11px; border: none; background: transparent;")

        layout.addWidget(self.icon_lbl, 1)
        layout.addWidget(self.name_lbl)

        self.set_selected(False) 

    def set_selected(self, is_selected):
        # 🚀 CHANGED: Connected to ThemeManager colors
        if is_selected:
            self.setStyleSheet(f"#FileCard {{ background-color: rgba(79, 209, 197, 0.15); border: 1px solid {ThemeColors.ACCENT_TEAL}; border-radius: 6px; }}")
        else:
            self.setStyleSheet(f"""
                #FileCard {{ background-color: {ThemeColors.BG_INPUT}; border: 1px solid {ThemeColors.BORDER_DEFAULT}; border-radius: 6px; }}
                #FileCard:hover {{ background-color: {ThemeColors.BORDER_ACTIVE}; border: 1px solid {ThemeColors.ACCENT_BLUE}; }}
            """)

    def mousePressEvent(self, event):
        self.clicked_card.emit(self, self.file_path)
        super().mousePressEvent(event)

class SliderWidgetContainer(QWidget):
    clicked_empty = Signal()
    def mousePressEvent(self, event):
        self.clicked_empty.emit()
        super().mousePressEvent(event)

class GlobalSearchOverlay(QFrame):
    close_requested = Signal()
    file_selected = Signal(str, str)
    
    find_next = Signal(str, bool)
    find_prev = Signal(str, bool)
    replace_current = Signal(str, str, bool)
    replace_all = Signal(str, str, bool)
    search_updated = Signal(str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)
        self.setObjectName("GlobalSearch")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True) 
        self.user_moved = False 
        self.project_root = None
        self.worker = None
        self.setMinimumSize(650, 230) 

        # 🚀 REMOVED: Huge global stylesheet block. We just style the main frame and close button locally.
        self.setStyleSheet(f"""
            #GlobalSearch {{ background-color: {ThemeColors.BG_PANEL}; border: 1px solid {ThemeColors.BORDER_ACTIVE}; border-radius: 8px; }}
            #SliderWidget {{ background: transparent; }}
            QLabel {{ color: {ThemeColors.TEXT_MUTED}; font-size: 12px; margin-right: 5px; background: transparent; border: none; }}
            QPushButton#closeBtn:hover {{ background-color: {ThemeColors.ERROR}; color: {ThemeColors.BG_BASE}; border: none; }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # --- 1. Files Slider ---
        self.slider_layout = QHBoxLayout()
        self.slider_layout.setContentsMargins(0, 0, 0, 0)
        self.slider_layout.setSpacing(10)
        self.slider_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.slider_widget = SliderWidgetContainer()
        self.slider_widget.setObjectName("SliderWidget")
        self.slider_widget.setLayout(self.slider_layout)
        self.slider_widget.clicked_empty.connect(self.deselect_all_cards)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setWidget(self.slider_widget)
        self.scroll_area.setFixedHeight(120)

        top_row = QHBoxLayout()
        self.btn_scroll_left = QPushButton("❮")
        self.btn_scroll_left.clicked.connect(lambda: self.scroll_area.horizontalScrollBar().setValue(self.scroll_area.horizontalScrollBar().value() - 150))
        
        self.btn_scroll_right = QPushButton("❯")
        self.btn_scroll_right.clicked.connect(lambda: self.scroll_area.horizontalScrollBar().setValue(self.scroll_area.horizontalScrollBar().value() + 150))
        
        top_row.addWidget(self.btn_scroll_left)
        top_row.addWidget(self.scroll_area)
        top_row.addWidget(self.btn_scroll_right)
        main_layout.addLayout(top_row)
        
        self.status_label = QLabel("Type and press Enter to search in project.")
        main_layout.addWidget(self.status_label)

        # --- 2. Search bar similar to Find ---
        row_find = QHBoxLayout()
        row_find.setSpacing(4)

        self.btn_toggle = QPushButton("⯈")
        self.btn_toggle.setFixedSize(28, 28)
        self.btn_toggle.setToolTip("Toggle Replace")
        self.btn_toggle.clicked.connect(self.toggle_replace)
        row_find.addWidget(self.btn_toggle)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Global Search...")
        self.search_edit.returnPressed.connect(self.perform_search)
        self.search_edit.textChanged.connect(self._on_text_changed)
        row_find.addWidget(self.search_edit)

        self.count_label = QLabel("0 results")
        row_find.addWidget(self.count_label)

        self.btn_next = QPushButton("↓")
        self.btn_next.setFixedSize(28, 28)
        
        self.btn_prev = QPushButton("↑")
        self.btn_prev.setFixedSize(28, 28)

        self.btn_case = QPushButton("Aa")
        self.btn_case.setCheckable(True)
        self.btn_case.setFixedSize(28, 28)
        self.btn_case.toggled.connect(self._on_text_changed)

        self.btn_close = QPushButton("✕")
        self.btn_close.setObjectName("closeBtn")
        self.btn_close.setFixedSize(28, 28)

        row_find.addWidget(self.btn_next)
        row_find.addWidget(self.btn_prev)
        row_find.addWidget(self.btn_case)
        row_find.addWidget(self.btn_close)

        main_layout.addLayout(row_find)

        # --- 3. Replace section ---
        self.replace_widget = QWidget()
        row_replace = QHBoxLayout(self.replace_widget)
        row_replace.setContentsMargins(32, 0, 0, 0)
        row_replace.setSpacing(4)

        self.replace_edit = QLineEdit()
        self.replace_edit.setPlaceholderText("Replace in current file")
        row_replace.addWidget(self.replace_edit)

        self.btn_replace = QPushButton("Replace")
        # 🚀 REMOVED: Manual button stylesheets.
        
        self.btn_replace_all = QPushButton("All")
        # 🚀 REMOVED: Manual button stylesheets.

        row_replace.addWidget(self.btn_replace)
        row_replace.addWidget(self.btn_replace_all)

        main_layout.addWidget(self.replace_widget)
        self.replace_widget.setVisible(False)

        self.btn_next.clicked.connect(self._on_next)
        self.btn_prev.clicked.connect(self._on_prev)
        self.btn_replace.clicked.connect(self._on_replace)
        self.btn_replace_all.clicked.connect(self._on_replace_all)
        self.btn_close.clicked.connect(self.hide_overlay)

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
        is_vis = self.replace_widget.isVisible()
        self.replace_widget.setVisible(not is_vis)
        self.btn_toggle.setText("⯆" if not is_vis else "⯈")
        self.adjustSize()

    def _on_text_changed(self):
        text = self.search_edit.text()
        self.search_updated.emit(text, self.btn_case.isChecked())

    def _on_next(self):
        if self.search_edit.text():
            self.find_next.emit(self.search_edit.text(), self.btn_case.isChecked())

    def _on_prev(self):
        if self.search_edit.text():
            self.find_prev.emit(self.search_edit.text(), self.btn_case.isChecked())

    def _on_replace(self):
        if self.search_edit.text():
            self.replace_current.emit(self.search_edit.text(), self.replace_edit.text(), self.btn_case.isChecked())

    def _on_replace_all(self):
        if self.search_edit.text():
            self.replace_all.emit(self.search_edit.text(), self.replace_edit.text(), self.btn_case.isChecked())

    def set_project_root(self, root):
        self.project_root = root
        self.clear_slider()
        self.search_edit.clear()
        self.status_label.setText("Ready to search.")

    def clear_slider(self):
        while self.slider_layout.count():
            item = self.slider_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def deselect_all_cards(self):
        for i in range(self.slider_layout.count()):
            widget = self.slider_layout.itemAt(i).widget()
            if isinstance(widget, FileCard):
                widget.set_selected(False)

    def perform_search(self):
        text = self.search_edit.text().strip()
        self.clear_slider()
        
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
            
        if not text or not self.project_root:
            self.status_label.setText("Please enter a search term.")
            return

        self.status_label.setText("Searching across project... Please wait.")
        
        self.worker = SearchWorker(self.project_root, text)
        self.worker.match_found.connect(lambda fp, t=text: self._add_match(fp, t))
        self.worker.finished_search.connect(self._on_search_finished)
        self.worker.start()

    def _add_match(self, file_path, search_term):
        card = FileCard(file_path)
        card.clicked_card.connect(lambda c, path=file_path, t=search_term: self._handle_card_click(c, path, t))
        self.slider_layout.addWidget(card)

    def _on_search_finished(self, count):
        if count > 0:
            self.status_label.setText(f"Found matches in {count} files. (Click to open)")
        else:
            self.status_label.setText("No matches found in project.")

    def _handle_card_click(self, clicked_card, file_path, search_term):
        for i in range(self.slider_layout.count()):
            widget = self.slider_layout.itemAt(i).widget()
            if isinstance(widget, FileCard):
                widget.set_selected(widget == clicked_card)
        
        self.file_selected.emit(file_path, search_term)

    def hide_overlay(self):
        self.setVisible(False)
        self.search_updated.emit("", False)
        self.close_requested.emit()